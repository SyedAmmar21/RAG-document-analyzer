import logging
import re
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from pathlib import Path

import trafilatura
from tavily import TavilyClient

from app.core.config import TAVILY_API_KEY
from app.db.database import get_connection
from app.services.document_ingestion_service import process_document_pipeline
from app.core.paths import NEWS_ARTICLES_DIR, to_relative_storage_path, resolve_storage_path, ensure_directories_exist


logger = logging.getLogger(__name__)

MAX_NEWS_ARTICLES = 10
MIN_ARTICLE_CHARACTERS = 500
TRACKING_QUERY_PREFIXES = ("utm_",)
TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
}

# Focused search queries for different gold market drivers
GOLD_SEARCH_QUERIES = [
    "gold prices latest today Federal Reserve interest rates",  # Economic factors
    "central banks buying gold reserves 2024",  # Institutional demand
    "gold mining production disruption supply",  # Supply issues
    "geopolitical tensions safe haven gold demand",  # Geopolitical factors
]

def _get_tavily_client() -> TavilyClient:
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not configured.")

    return TavilyClient(api_key=TAVILY_API_KEY)


def search_gold_news(max_results: int = MAX_NEWS_ARTICLES) -> Dict[str, Any]:
    """
    Search for relevant gold news using multiple focused queries.
    
    Searches across different gold market drivers:
    - Economic indicators (Fed, rates, inflation)
    - Central bank activity
    - Supply disruptions
    - Geopolitical factors
    """
    try:
        client = _get_tavily_client()
        all_results = []
        
        # Search multiple focused queries for better relevance
        for query in GOLD_SEARCH_QUERIES:
            try:
                response = client.search(
                    query=query,
                    topic="news",
                    max_results=max_results // len(GOLD_SEARCH_QUERIES) + 1,  # Distribute results
                    days=1,
                    search_depth="advanced",
                    include_answer=False,
                )
                all_results.extend(response.get("results", []))
            except Exception as e:
                logger.warning("Search failed for query '%s': %s", query, str(e))
                continue
        
        # Remove duplicates by URL while preserving order
        seen_urls = set()
        unique_results = []
        for result in all_results:
            url = result.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        # Sort by relevance score (if available) and return top results
        if unique_results:
            unique_results.sort(
                key=lambda x: x.get("score", 0),
                reverse=True
            )
        
        return {
            "results": unique_results[:max_results],
            "total_results": len(unique_results),
        }
    except Exception as error:
        logger.exception("Tavily gold news search failed")
        return {
            "results": [],
            "error": str(error),
        }


def _is_valid_article_text(text: Optional[str]) -> bool:
    return bool(text and len(text.strip()) >= MIN_ARTICLE_CHARACTERS)


def _extract_with_trafilatura(url: str) -> Optional[str]:
    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        extracted_text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
        )

        if not _is_valid_article_text(extracted_text):
            return None

        return extracted_text.strip()
    except Exception:
        logger.exception("Trafilatura extraction failed for %s", url)
        return None


def _extract_with_tavily(url: str) -> Optional[str]:
    try:
        client = _get_tavily_client()
        response = client.extract(
            urls=url,
            extract_depth="advanced",
            format="text",
        )

        for result in response.get("results", []):
            raw_content = result.get("raw_content")
            if _is_valid_article_text(raw_content):
                return raw_content.strip()

        if response.get("failed_results"):
            logger.info("Tavily extract failed for %s: %s", url, response["failed_results"])

        return None
    except Exception:
        logger.exception("Tavily extraction failed for %s", url)
        return None


def extract_article_text(url: str) -> Optional[str]:
    extracted_text = _extract_with_trafilatura(url)

    if extracted_text:
        return extracted_text

    logger.info("Falling back to Tavily Extract for %s", url)
    return _extract_with_tavily(url)


def _canonicalize_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None

    parsed = urlsplit(url.strip())

    if not parsed.scheme or not parsed.netloc:
        return url.strip().rstrip("/")

    query_items = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lower_key = key.lower()
        if lower_key in TRACKING_QUERY_KEYS:
            continue
        if any(lower_key.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES):
            continue
        query_items.append((key, value))

    normalized_path = parsed.path.rstrip("/") or "/"
    normalized_query = urlencode(query_items, doseq=True)

    return urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        normalized_path,
        normalized_query,
        "",
    ))


def _get_existing_news_urls() -> set[str]:
    """Get all URLs from existing news articles in the database."""
    ensure_directories_exist()
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT file_path
        FROM documents
        WHERE file_path LIKE ?
        """,
        ("news_articles/%",)
    )
    rows = cursor.fetchall()
    conn.close()

    existing_urls = set()

    for row in rows:
        relative_path = row["file_path"]
        if not relative_path:
            continue
        
        try:
            # Resolve to absolute path
            absolute_path = resolve_storage_path(relative_path)
            
            if not absolute_path.exists():
                continue
            
            with open(absolute_path, "r", encoding="utf-8") as file:
                for _ in range(5):
                    line = file.readline()
                    if not line:
                        break
                    if line.startswith("Source URL:"):
                        canonical_url = _canonicalize_url(
                            line.replace("Source URL:", "", 1).strip()
                        )
                        if canonical_url:
                            existing_urls.add(canonical_url)
                        break
        except OSError:
            logger.warning("Could not inspect existing news file for URL: %s", relative_path)

    return existing_urls


def _sanitize_title(title: str) -> str:
    normalized = re.sub(r"[^\w\s.-]", "_", title or "Untitled")
    normalized = re.sub(r"\s+", "_", normalized).strip("._ ")
    return (normalized or "Untitled")[:80]


def save_article_as_txt(
    title: str,
    text: str,
    url: Optional[str] = None,
    published_date: Optional[str] = None,
) -> str:
    """
    Save a news article as a text file.
    
    Args:
        title: Article title
        text: Article content
        url: Source URL
        published_date: Publication date
    
    Returns:
        Relative path to the saved article (for database storage)
    """
    ensure_directories_exist()

    filename = f"{_sanitize_title(title)}_{uuid.uuid4().hex[:8]}.txt"
    absolute_path = NEWS_ARTICLES_DIR / filename

    header = [
        f"Title: {title or 'Untitled'}",
    ]

    if published_date:
        header.append(f"Published date: {published_date}")

    if url:
        header.append(f"Source URL: {url}")

    content = "\n".join(header) + "\n\n" + text.strip()

    with open(absolute_path, "w", encoding="utf-8") as file:
        file.write(content)

    # Return relative path for database storage
    relative_path = to_relative_storage_path(absolute_path)
    return relative_path


def _domain_name_from_pipeline_result(pipeline_result: Dict[str, Any]) -> Optional[str]:
    assigned_domain = pipeline_result.get("assigned_domain")
    if assigned_domain:
        return assigned_domain.get("domain_name") or assigned_domain.get("name")

    domain_suggestion = pipeline_result.get("domain_suggestion")
    if domain_suggestion:
        return domain_suggestion.get("domain_name") or domain_suggestion.get("name")

    return None


def _article_result(
    title: str,
    url: Optional[str],
    status: str,
    success: bool,
    error: Optional[str] = None,
    reason: Optional[str] = None,
    **extra,
) -> Dict[str, Any]:
    """Create a standardized article result dict."""
    result = {
        "title": title or "Untitled",
        "url": url,
        "status": status,
        "success": success,
    }
    if error:
        result["error"] = error
    if reason:
        result["reason"] = reason
    result.update(extra)
    return result


def _should_skip_duplicate(url: Optional[str], title: str, seen_urls: set, seen_titles: set) -> Optional[str]:
    """Check if article is duplicate. Returns skip reason or None."""
    if not url:
        return "Missing article URL."
    
    canonical_url = _canonicalize_url(url)
    if canonical_url and canonical_url in seen_urls:
        return "Duplicate article URL already processed."
    
    normalized_title = re.sub(r"\s+", " ", title).strip().casefold()
    if normalized_title and normalized_title in seen_titles:
        return "Duplicate article title in Tavily results."
    
    return None


def _track_article(url: Optional[str], title: str, seen_urls: set, seen_titles: set) -> None:
    """Add article to tracking sets."""
    canonical_url = _canonicalize_url(url)
    if canonical_url:
        seen_urls.add(canonical_url)
    
    normalized_title = re.sub(r"\s+", " ", title).strip().casefold()
    if normalized_title:
        seen_titles.add(normalized_title)


def _build_ingestion_summary(
    processed: List[Dict[str, Any]],
    failed: List[Dict[str, Any]],
    skipped: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build standardized ingestion summary response."""
    return {
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "total_processed": len(processed),
        "total_failed": len(failed),
        "total_skipped": len(skipped),
    }


def ingest_latest_gold_news(max_results: int = MAX_NEWS_ARTICLES) -> Dict[str, Any]:
    """Ingest latest gold news articles and process through document pipeline."""
    response = search_gold_news(max_results=max_results)
    processed: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    seen_urls = _get_existing_news_urls()
    seen_titles: set[str] = set()

    if response.get("error"):
        failed.append(
            _article_result(
                title="Tavily search",
                url=None,
                status="failed",
                success=False,
                error=response["error"],
            )
        )
        return _build_ingestion_summary(processed, failed, skipped)

    results = response.get("results") or []

    for article in results[:max_results]:
        title = article.get("title") or "Untitled"
        url = article.get("url")
        published_date = (
            article.get("published_date")
            or article.get("publishedDate")
            or article.get("date")
        )

        skip_reason = _should_skip_duplicate(url, title, seen_urls, seen_titles)
        if skip_reason:
            skipped.append(
                _article_result(
                    title=title,
                    url=url,
                    status="skipped",
                    success=True,
                    reason=skip_reason,
                )
            )
            continue

        _track_article(url, title, seen_urls, seen_titles)
        logger.info("Processing gold news article: %s", title)

        extracted_text = extract_article_text(url)
        if not extracted_text:
            failed.append(
                _article_result(
                    title=title,
                    url=url,
                    status="failed",
                    success=False,
                    error="Could not extract enough article text.",
                )
            )
            continue

        try:
            file_path = save_article_as_txt(
                title=title,
                text=extracted_text,
                url=url,
                published_date=published_date,
            )

            pipeline_result = process_document_pipeline(
                file_path=file_path,
                original_filename=Path(file_path).name,
            )

            processed.append(
                _article_result(
                    title=title,
                    url=url,
                    status="processed",
                    success=True,
                    document_id=pipeline_result["document_id"],
                    file_name=pipeline_result["file_name"],
                    file_path=file_path,
                    domain=_domain_name_from_pipeline_result(pipeline_result),
                    domain_details=(
                        pipeline_result.get("assigned_domain")
                        or pipeline_result.get("domain_suggestion")
                    ),
                    metadata=pipeline_result.get("metadata_suggestions"),
                )
            )
        except Exception as error:
            logger.exception("Gold news ingestion failed for %s", title)
            failed.append(
                _article_result(
                    title=title,
                    url=url,
                    status="failed",
                    success=False,
                    error=str(error),
                )
            )

    return _build_ingestion_summary(processed, failed, skipped)
