import logging

from fastapi import APIRouter

from app.services.news_ingestion_service import ingest_latest_gold_news
from app.services.scheduler_service import get_latest_scheduled_result, clear_latest_scheduled_result


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])


@router.post("/ingest-latest")
async def ingest_latest_news():
    logger.info("Starting latest gold news ingestion")
    return ingest_latest_gold_news()


@router.get("/scheduled-summary")
async def get_scheduled_summary():
    """
    Return the latest scheduled ingestion summary for frontend polling.
    Clears the stored result so it only shows once.
    """
    summary = get_latest_scheduled_result()
    if summary:
        clear_latest_scheduled_result()
    return summary
