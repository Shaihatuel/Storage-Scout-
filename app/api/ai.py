"""
API routes for AI recommendation engine.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AIRecommendation, Listing
from app.ai.recommender import generate_recommendation

router = APIRouter()


@router.post("/recommend/{listing_id}")
def recommend(listing_id: int, db: Session = Depends(get_db)):
    """Generate or refresh an AI recommendation for a listing."""
    listing = db.get(Listing, listing_id)
    if not listing:
        raise HTTPException(404, "Listing not found")

    rec_data = generate_recommendation(listing, db)

    existing = db.query(AIRecommendation).filter(
        AIRecommendation.listing_id == listing_id
    ).first()

    if existing:
        for k, v in rec_data.items():
            setattr(existing, k, v)
        db.commit()
        db.refresh(existing)
        return _rec_dict(existing)

    rec = AIRecommendation(listing_id=listing_id, **rec_data)
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return _rec_dict(rec)


@router.post("/recommend-all")
def recommend_all(use_vision: bool = False, db: Session = Depends(get_db)):
    """Generate recommendations for every listing that doesn't have one yet."""
    from app.models import Listing
    listings = db.query(Listing).all()
    created = updated = skipped = 0
    for listing in listings:
        try:
            rec_data = generate_recommendation(listing, db, use_vision=use_vision)
            existing = db.query(AIRecommendation).filter(
                AIRecommendation.listing_id == listing.id
            ).first()
            if existing:
                for k, v in rec_data.items():
                    setattr(existing, k, v)
                updated += 1
            else:
                db.add(AIRecommendation(listing_id=listing.id, **rec_data))
                created += 1
        except Exception as exc:
            skipped += 1
            import logging
            logging.getLogger(__name__).warning(f"Skipped listing {listing.id}: {exc}")
    db.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "total": len(listings)}


@router.get("/recommendations")
def list_recommendations(db: Session = Depends(get_db)):
    recs = db.query(AIRecommendation).order_by(AIRecommendation.confidence_score.desc()).all()
    return [_rec_dict(r) for r in recs]


def _rec_dict(rec: AIRecommendation) -> dict:
    return {
        "id": rec.id,
        "listing_id": rec.listing_id,
        "recommendation": rec.recommendation,
        "confidence_score": rec.confidence_score,
        "estimated_value": rec.estimated_value,
        "suggested_max_bid": rec.suggested_max_bid,
        "reasoning": rec.reasoning,
        "model_version": rec.model_version,
        "generated_at": rec.generated_at.isoformat() if rec.generated_at else None,
    }
