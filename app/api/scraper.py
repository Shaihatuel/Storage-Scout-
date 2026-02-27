"""
API route for running the StorageTreasures scraper synchronously.

POST /api/scraper/run
  Body: { state, zip_code, radius_miles, max_pages, auction_types }
  Returns: { new_listings, total_scraped, recommendations_generated }

The endpoint blocks until the scrape finishes (typically 15-120 seconds
depending on page count, since Playwright is used for the first page).
After scraping, recommendations are automatically generated for all new
listings that don't already have one.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Mapping from human-readable auction type name to StorageTreasures filter_type int
_AUCTION_TYPE_MAP = {
    "lien":            "1",
    "1":               "1",
    "manager_special": "3",
    "manager special": "3",
    "3":               "3",
    "private":         "2",
    "private_seller":  "2",
    "non_lien":        "2",
    "2":               "2",
    "charity":         "4",
    "4":               "4",
}


class ScrapeRequest(BaseModel):
    state:         Optional[str]       = None
    zip_code:      Optional[str]       = None
    radius_miles:  int                 = 50
    max_pages:     int                 = 5
    auction_types: List[str]           = ["1", "2", "3", "4"]


@router.post("/run")
def run_scraper(data: ScrapeRequest):
    """
    Run the scraper synchronously and return results.

    This endpoint blocks for the duration of the scrape.  The caller
    (dashboard) should show a loading indicator while waiting.
    """
    from app.scraper.storage_treasures import StorageTreasuresScraper
    from app.database import SessionLocal

    # Map any human-readable auction type names → numeric IDs, dedupe
    type_ids = list({
        _AUCTION_TYPE_MAP.get(t.lower().strip(), t)
        for t in (data.auction_types or ["1", "2", "3", "4"])
    })
    filter_types = ",".join(sorted(type_ids))

    db = SessionLocal()
    try:
        scraper = StorageTreasuresScraper()
        new_count, total = scraper.fetch_and_save(
            state        = data.state    or None,
            zip_code     = data.zip_code or None,
            radius_miles = data.radius_miles,
            max_pages    = data.max_pages,
            filter_types = filter_types,
            db           = db,
        )
        recs_created = _auto_recommend_new(db) if new_count > 0 else 0
        return {
            "new_listings":             new_count,
            "total_scraped":            total,
            "recommendations_generated": recs_created,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        db.close()


def _auto_recommend_new(db) -> int:
    """Generate recommendations for any listing that doesn't have one yet."""
    from app.models import Listing, AIRecommendation
    from app.ai.recommender import generate_recommendation

    listings_needing_recs = (
        db.query(Listing)
        .outerjoin(AIRecommendation, AIRecommendation.listing_id == Listing.id)
        .filter(AIRecommendation.id.is_(None))
        .all()
    )

    created = 0
    for listing in listings_needing_recs:
        try:
            rec_data = generate_recommendation(listing, db)
            db.add(AIRecommendation(listing_id=listing.id, **rec_data))
            created += 1
        except Exception as exc:
            logger.warning(f"Auto-rec skipped listing {listing.id}: {exc}")

    if created:
        db.commit()
    return created
