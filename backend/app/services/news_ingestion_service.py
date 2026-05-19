import logging
import os
import re
import uuid
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import trafilatura
from tavily import TavilyClient

from app.core.config import TAVILY_API_KEY
from app.db.database import get_connection
from app.services.document_ingestion_service import process_document_pipeline


logger = logging.getLogger(__name__)

NEWS_STORAGE_DIR = os.path.join("storage", "news_articles")
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


def _get_tavily_client() -> TavilyClient:
    if not TAVILY_API_KEY:
        raise RuntimeError("TAVILY_API_KEY is not configured.")

    return TavilyClient(api_key=TAVILY_API_KEY)


def search_gold_news(max_results: int = MAX_NEWS_ARTICLES) -> Dict[str, Any]:
    try:
        client = _get_tavily_client()
        return client.search(
            query=(
                "latest gold market news gold price Federal Reserve "
                "inflation central banks geopolitics"
            ),
            topic="news",
            max_results=max_results,
        )
    except Exception as error:
        logger.exception("Tavily gold news search failed")
        return {
            "results": [],
            "error": str(error),
        }


def extract_article_text(url: str) -> Optional[str]:
    try:
        downloaded = trafilatura.fetch_url(url)

        if not downloaded:
            return None

        extracted_text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
        )

        if not extracted_text or len(extracted_text.strip()) < MIN_ARTICLE_CHARACTERS:
            return None

        return extracted_text.strip()
    except Exception:
        logger.exception("Article extraction failed for %s", url)
        return None


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
    if not os.path.isdir(NEWS_STORAGE_DIR):
        return set()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT file_path
        FROM documents
        WHERE file_path LIKE ?
        """,
        (f"%{NEWS_STORAGE_DIR.replace(os.sep, '%')}%",)
    )
    rows = cursor.fetchall()
    conn.close()

    existing_urls = set()

    for row in rows:
        file_path = row["file_path"]
        if not file_path or not os.path.exists(file_path):
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as file:
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
            logger.warning("Could not inspect existing news file for URL: %s", file_path)

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
    os.makedirs(NEWS_STORAGE_DIR, exist_ok=True)

    filename = f"{_sanitize_title(title)}_{uuid.uuid4().hex[:8]}.txt"
    file_path = os.path.join(NEWS_STORAGE_DIR, filename)

    header = [
        f"Title: {title or 'Untitled'}",
    ]

    if published_date:
        header.append(f"Published date: {published_date}")

    if url:
        header.append(f"Source URL: {url}")

    content = "\n".join(header) + "\n\n" + text.strip()

    with open(file_path, "w", encoding="utf-8") as file:
        file.write(content)

    return file_path


def _domain_name_from_pipeline_result(pipeline_result: Dict[str, Any]) -> Optional[str]:
    assigned_domain = pipeline_result.get("assigned_domain")
    if assigned_domain:
        return assigned_domain.get("domain_name") or assigned_domain.get("name")

    domain_suggestion = pipeline_result.get("domain_suggestion")
    if domain_suggestion:
        return domain_suggestion.get("domain_name") or domain_suggestion.get("name")

    return None


def _failure_result(
    title: str,
    url: Optional[str],
    reason: str,
) -> Dict[str, Any]:
    return {
        "title": title or "Untitled",
        "url": url,
        "status": "failed",
        "success": False,
        "error": reason,
    }


def _skipped_result(
    title: str,
    url: Optional[str],
    reason: str,
) -> Dict[str, Any]:
    return {
        "title": title or "Untitled",
        "url": url,
        "status": "skipped",
        "success": True,
        "reason": reason,
    }


def ingest_latest_gold_news(max_results: int = MAX_NEWS_ARTICLES) -> Dict[str, Any]:
    response = search_gold_news(max_results=max_results)
    processed: List[Dict[str, Any]] = []
    failed: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    seen_urls = _get_existing_news_urls()
    seen_titles = set()

    if response.get("error"):
        failed.append(
            _failure_result(
                title="Tavily search",
                url=None,
                reason=response["error"],
            )
        )
        return {
            "processed": processed,
            "failed": failed,
            "skipped": skipped,
            "total_processed": 0,
            "total_failed": len(failed),
            "total_skipped": 0,
        }

    results = response.get("results") or []

    for article in results[:max_results]:
        title = article.get("title") or "Untitled"
        url = article.get("url")
        canonical_url = _canonicalize_url(url)
        normalized_title = re.sub(r"\s+", " ", title).strip().casefold()
        published_date = (
            article.get("published_date")
            or article.get("publishedDate")
            or article.get("date")
        )

        if not url:
            failed.append(_failure_result(title, url, "Missing article URL."))
            continue

        if canonical_url and canonical_url in seen_urls:
            skipped.append(
                _skipped_result(
                    title,
                    url,
                    "Duplicate article URL already processed.",
                )
            )
            continue

        if normalized_title and normalized_title in seen_titles:
            skipped.append(
                _skipped_result(
                    title,
                    url,
                    "Duplicate article title in Tavily results.",
                )
            )
            continue

        if canonical_url:
            seen_urls.add(canonical_url)
        if normalized_title:
            seen_titles.add(normalized_title)

        logger.info("Processing gold news article: %s", title)

        extracted_text = extract_article_text(url)

        if not extracted_text:
            failed.append(
                _failure_result(
                    title,
                    url,
                    "Could not extract enough article text.",
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
                original_filename=os.path.basename(file_path),
            )

            processed.append({
                "title": title,
                "url": url,
                "status": "processed",
                "success": True,
                "document_id": pipeline_result["document_id"],
                "file_name": pipeline_result["file_name"],
                "file_path": file_path,
                "domain": _domain_name_from_pipeline_result(pipeline_result),
                "domain_details": (
                    pipeline_result.get("assigned_domain")
                    or pipeline_result.get("domain_suggestion")
                ),
                "metadata": pipeline_result.get("metadata_suggestions"),
            })
        except Exception as error:
            logger.exception("Gold news ingestion failed for %s", title)
            failed.append(_failure_result(title, url, str(error)))

    return {
        "processed": processed,
        "failed": failed,
        "skipped": skipped,
        "total_processed": len(processed),
        "total_failed": len(failed),
        "total_skipped": len(skipped),
    }
