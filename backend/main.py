from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.documents import router as documents_router
from app.routers.ingest import router as ingest_router
from app.routers.news import router as news_router
from app.routers.query import router as query_router
from app.db.database import init_db
from app.services.scheduler_service import start_scheduler, stop_scheduler


app = FastAPI()
init_db()

app.include_router(ingest_router)
app.include_router(news_router)
app.include_router(query_router)
app.include_router(documents_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Start scheduler when FastAPI starts."""
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler when FastAPI shuts down."""
    stop_scheduler()
