from tavily import TavilyClient
from app.core.config import TAVILY_API_KEY
import trafilatura
import os
import uuid
from datetime import datetime

#STORE DOWNLOADED NEWS
NEWS_STORAGE_DIR = "storage/news_articles"

os.makedirs(NEWS_STORAGE_DIR, exist_ok=True)

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def search_gold_news():

    response = tavily_client.search(
        query="latest gold market news",
        topic="news",
        max_results=5
    )

    return response

def extract_article_text(url: str):

    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return None

    extracted_text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=False
    )

    return extracted_text

def save_article_as_txt(title: str, text: str):

    safe_title = (
        title
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        [:80]
    )

    filename = f"{safe_title}_{uuid.uuid4().hex[:8]}.txt"

    file_path = os.path.join(
        NEWS_STORAGE_DIR,
        filename
    )

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)

    return file_path