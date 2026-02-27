"""
API routes for listing management.
"""
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import nulls_last
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.models import Listing, AuctionStatus, AIRecommendation, BidRecord, ListingImage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
def get_listings(
    status: Optional[AuctionStatus] = None,
    state: Optional[str] = None,
    limit: int = Query(200, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    from datetime import datetime
    q = db.query(Listing).filter(
        (Listing.auction_end_time == None) | (Listing.auction_end_time > datetime.utcnow())
    )
    if status:
        q = q.filter(Listing.status == status)
    if state:
        q = q.filter(Listing.state == state)
    total = q.count()

    # Sort by AI score descending; listings with no recommendation go last
    q = q.outerjoin(AIRecommendation, AIRecommendation.listing_id == Listing.id)
    items = (
        q.order_by(nulls_last(AIRecommendation.confidence_score.desc()))
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {"total": total, "items": [_listing_dict(l) for l in items]}


@router.get("/{listing_id}")
def get_listing(listing_id: int, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    return _listing_dict(listing, full=True)


@router.patch("/{listing_id}/status")
def update_status(listing_id: int, status: AuctionStatus, db: Session = Depends(get_db)):
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    listing.status = status
    db.commit()
    return {"id": listing_id, "status": status}


@router.patch("/{listing_id}/watch")
def toggle_watch(listing_id: int, db: Session = Depends(get_db)):
    """Toggle the watched/starred state of a listing."""
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    listing.watched = not bool(listing.watched)
    db.commit()
    return {"id": listing_id, "watched": listing.watched}


class NotesBody(BaseModel):
    notes: Optional[str] = None


@router.patch("/{listing_id}/notes")
def update_notes(listing_id: int, body: NotesBody, db: Session = Depends(get_db)):
    """Save personal notes for a listing."""
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    listing.notes = body.notes
    db.commit()
    return {"id": listing_id, "notes": listing.notes}


@router.post("/{listing_id}/bid-placed")
def toggle_bid_placed(listing_id: int, db: Session = Depends(get_db)):
    """Toggle an 'I bid this' marker. Creates or removes a BidRecord."""
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    existing = db.query(BidRecord).filter(BidRecord.listing_id == listing_id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"id": listing_id, "has_bid": False}
    db.add(BidRecord(listing_id=listing_id, max_bid=0))
    db.commit()
    return {"id": listing_id, "has_bid": True}


@router.post("/{listing_id}/fetch-images")
def fetch_images(listing_id: int, db: Session = Depends(get_db)):
    """Use Playwright to scrape all gallery images from the listing's ST page."""
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if not listing.url:
        raise HTTPException(400, "Listing has no URL")

    try:
        urls: List[str] = asyncio.run(_scrape_listing_images(listing.url))
    except Exception as exc:
        logger.error(f"fetch-images scrape failed for listing {listing_id}: {exc}")
        raise HTTPException(500, f"Image scrape failed: {exc}")

    existing_urls = {img.url for img in listing.images}
    new_count = 0
    for i, url in enumerate(urls):
        if url not in existing_urls:
            db.add(ListingImage(
                listing_id  = listing_id,
                url         = url,
                order_index = len(existing_urls) + new_count,
            ))
            existing_urls.add(url)
            new_count += 1

    if new_count:
        db.commit()
        db.refresh(listing)

    imgs = sorted(listing.images, key=lambda x: x.order_index)
    return {"images": [{"url": img.url, "order": img.order_index} for img in imgs]}


async def _scrape_listing_images(listing_url: str) -> List[str]:
    """Visit a StorageTreasures listing page and intercept all CDN image URLs."""
    from playwright.async_api import async_playwright

    CDN = "media.st-prd-1.aws.storagetreasures.com"
    seen: List[str] = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        ctx = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )
        page = await ctx.new_page()

        async def on_response(resp) -> None:
            u = resp.url
            if CDN in u and u not in seen:
                if any(u.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
                    seen.append(u)

        page.on("response", on_response)

        try:
            await page.goto(listing_url, wait_until="networkidle", timeout=35000)
            # Also harvest src attributes of any CDN img elements
            srcs: List[str] = await page.eval_on_selector_all(
                "img", "els => els.map(e => e.src)"
            )
            for src in srcs:
                if CDN in src and src not in seen:
                    seen.append(src)
        except Exception as exc:
            logger.warning(f"Playwright page load issue ({listing_url}): {exc}")
        finally:
            await browser.close()

    return seen


def _listing_dict(listing: Listing, full: bool = False) -> dict:
    # AI recommendation
    ai_rec = None
    if listing.ai_recommendation:
        r = listing.ai_recommendation
        ai_rec = {
            "recommendation":    r.recommendation,
            "confidence_score":  r.confidence_score,
            "estimated_value":   r.estimated_value,
            "suggested_max_bid": r.suggested_max_bid,
        }
        if full:
            ai_rec["reasoning"]      = r.reasoning
            ai_rec["model_version"]  = r.model_version

    # Images
    images = [
        {"url": img.url, "order": img.order_index}
        if not full else
        {"url": img.url, "local_path": img.local_path, "order": img.order_index}
        for img in listing.images
    ]

    d = {
        "id":               listing.id,
        "external_id":      listing.external_id,
        "url":              listing.url,
        "facility_name":    listing.facility_name,
        "city":             listing.city,
        "state":            listing.state,
        "unit_size":        listing.unit_size,
        "current_bid":      listing.current_bid,
        "bid_count":        listing.bid_count,
        "auction_end_time": listing.auction_end_time.isoformat() if listing.auction_end_time else None,
        "status":           listing.status,
        "scraped_at":       listing.scraped_at.isoformat() if listing.scraped_at else None,
        "watched":          bool(listing.watched),
        "has_bid":          listing.bid_record is not None,
        "images":           images,
        "ai_recommendation": ai_rec,
    }
    if full:
        d["description"]      = listing.description
        d["notes"]            = listing.notes
        d["facility_address"] = listing.facility_address
        d["zip_code"]         = listing.zip_code
        d["unit_number"]      = listing.unit_number
        d["unit_size_sqft"]   = listing.unit_size_sqft
        d["tags"] = [
            {"tag": t.tag, "confidence": t.confidence, "source": t.source}
            for t in listing.tags
        ]
    return d
