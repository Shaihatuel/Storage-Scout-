"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.database import init_db
from app.api import listings, bidding, pnl, analysis, ai, scraper


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Storage Scraper",
    description="Storage auction research, bidding assistant, and P&L tracker",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers — must be registered before the static file catch-all
app.include_router(listings.router, prefix="/api/listings", tags=["listings"])
app.include_router(bidding.router,  prefix="/api/bidding",  tags=["bidding"])
app.include_router(pnl.router,      prefix="/api/pnl",      tags=["pnl"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["analysis"])
app.include_router(ai.router,       prefix="/api/ai",       tags=["ai"])
app.include_router(scraper.router,  prefix="/api/scraper",  tags=["scraper"])


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "storage-scraper"}


# Static dashboard — mounted last so /api/* routes take priority
dashboard_dir = Path(__file__).parent / "dashboard" / "static"
if dashboard_dir.exists():
    app.mount("/", StaticFiles(directory=str(dashboard_dir), html=True), name="dashboard")
