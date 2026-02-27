"""
API routes for bid decision tracking.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import BidRecord, Listing

router = APIRouter()


class BidCreate(BaseModel):
    listing_id: int
    max_bid: float
    actual_bid: Optional[float] = None
    notes: Optional[str] = None


class BidUpdate(BaseModel):
    winning_bid: Optional[float] = None
    did_win: Optional[bool] = None
    actual_bid: Optional[float] = None
    notes: Optional[str] = None


@router.post("")
def create_bid(data: BidCreate, db: Session = Depends(get_db)):
    listing = db.get(Listing, data.listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")
    if db.query(BidRecord).filter(BidRecord.listing_id == data.listing_id).first():
        raise HTTPException(400, "Bid record already exists for this listing")
    record = BidRecord(
        listing_id=data.listing_id,
        max_bid=data.max_bid,
        actual_bid=data.actual_bid,
        notes=data.notes,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _bid_dict(record)


@router.patch("/{bid_id}")
def update_bid(bid_id: int, data: BidUpdate, db: Session = Depends(get_db)):
    record = db.get(BidRecord, bid_id)
    if not record:
        raise HTTPException(404, "Bid record not found")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(record, field, val)
    db.commit()
    db.refresh(record)
    return _bid_dict(record)


@router.get("/listing/{listing_id}")
def get_bid_for_listing(listing_id: int, db: Session = Depends(get_db)):
    record = db.query(BidRecord).filter(BidRecord.listing_id == listing_id).first()
    if not record:
        raise HTTPException(404, "No bid record for this listing")
    return _bid_dict(record)


def _bid_dict(record: BidRecord) -> dict:
    return {
        "id": record.id,
        "listing_id": record.listing_id,
        "max_bid": record.max_bid,
        "actual_bid": record.actual_bid,
        "winning_bid": record.winning_bid,
        "did_win": record.did_win,
        "notes": record.notes,
        "decision_at": record.decision_at.isoformat() if record.decision_at else None,
    }
