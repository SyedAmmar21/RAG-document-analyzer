import logging

from fastapi import APIRouter

from app.services.news_ingestion_service import ingest_latest_gold_news


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/news", tags=["news"])


@router.post("/ingest-latest")
async def ingest_latest_news():
    logger.info("Starting latest gold news ingestion")
    return ingest_latest_gold_news()
