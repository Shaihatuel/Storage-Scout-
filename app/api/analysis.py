"""
API routes for pattern analysis on winning vs losing units.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from collections import defaultdict
from app.database import get_db
from app.models import PnLEntry, Listing, ListingTagMap, BidRecord

router = APIRouter()


@router.get("/win-loss-by-tag")
def win_loss_by_tag(db: Session = Depends(get_db)):
    """Break down win rate and average net profit by unit tag."""
    rows = (
        db.query(ListingTagMap.tag, PnLEntry.net_profit)
        .join(Listing, Listing.id == ListingTagMap.listing_id)
        .join(PnLEntry, PnLEntry.listing_id == Listing.id)
        .all()
    )
    stats: dict = defaultdict(lambda: {"count": 0, "wins": 0, "total_net": 0.0})
    for tag, net in rows:
        key = tag.value if hasattr(tag, "value") else str(tag)
        stats[key]["count"] += 1
        stats[key]["total_net"] += net or 0.0
        if (net or 0) > 0:
            stats[key]["wins"] += 1

    result = []
    for tag, s in stats.items():
        result.append({
            "tag": tag,
            "count": s["count"],
            "win_rate": round(s["wins"] / s["count"], 3),
            "avg_net_profit": round(s["total_net"] / s["count"], 2),
            "total_net_profit": round(s["total_net"], 2),
        })
    return sorted(result, key=lambda x: x["avg_net_profit"], reverse=True)


@router.get("/win-loss-by-size")
def win_loss_by_size(db: Session = Depends(get_db)):
    """Break down win rate and profitability by unit size."""
    rows = (
        db.query(Listing.unit_size, PnLEntry.net_profit)
        .join(PnLEntry, PnLEntry.listing_id == Listing.id)
        .all()
    )
    stats: dict = defaultdict(lambda: {"count": 0, "wins": 0, "total_net": 0.0})
    for size, net in rows:
        key = size or "unknown"
        stats[key]["count"] += 1
        stats[key]["total_net"] += net or 0.0
        if (net or 0) > 0:
            stats[key]["wins"] += 1

    result = []
    for size, s in stats.items():
        result.append({
            "unit_size": size,
            "count": s["count"],
            "win_rate": round(s["wins"] / s["count"], 3),
            "avg_net_profit": round(s["total_net"] / s["count"], 2),
        })
    return sorted(result, key=lambda x: x["avg_net_profit"], reverse=True)


@router.get("/bid-efficiency")
def bid_efficiency(db: Session = Depends(get_db)):
    """Analyze how max bid vs winning bid correlates with profitability."""
    rows = (
        db.query(BidRecord.max_bid, BidRecord.winning_bid, BidRecord.did_win, PnLEntry.net_profit)
        .join(Listing, Listing.id == BidRecord.listing_id)
        .outerjoin(PnLEntry, PnLEntry.listing_id == Listing.id)
        .all()
    )
    result = []
    for max_bid, winning_bid, did_win, net in rows:
        if max_bid and winning_bid:
            result.append({
                "max_bid": max_bid,
                "winning_bid": winning_bid,
                "overbid_ratio": round(winning_bid / max_bid, 3),
                "did_win": did_win,
                "net_profit": net,
            })
    return result
