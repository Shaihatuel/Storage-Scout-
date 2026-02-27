"""
AI recommendation engine — beginner resale scoring model (heuristic-v3).

Designed for a beginner buyer reselling on eBay and Facebook Marketplace
in Florida. All criteria are additive from a base of 0.

Scoring criteria
────────────────
Auction type:
  Lien             +15
  Manager special  +5
  Charity          -5
  Private seller    0

Unit size (exact match on normalized size string):
  10x20  +20 · 10x15  +18 · 10x10  +15 · 5x10  +8 · 5x5  +2

Current bid:
  < $100       +15 · $100-200  +10 · $200-400  +5 · > $400  -10

Bid count:
  0-5 bids   +10 · 6-15 bids  +5 · 16-25 bids  0 · >25 bids  -10

Time remaining:
  > 24 hrs  +5 · 6-24 hrs  +3 · < 6 hrs  -5

Description keyword boosts (independent — all matching categories apply):
  tools / toolbox / dewalt / milwaukee / craftsman  +15
  electronics / tv / laptop / gaming                +10
  boxes / sealed / retail                           +10
  furniture / dresser / couch                        +5

Description keyword penalties:
  mattress                    -15
  clothes / clothing          -10
  trash / junk / empty        -20
  water / damage              -15
  No description at all        -5

No images  -10

Tiers
─────
  A+  85-100  → BUY
  A   70-84   → BUY
  B   55-69   → WATCH
  C   40-54   → RISKY
  D    0-39   → SKIP
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from app.models import Listing

logger = logging.getLogger(__name__)

MODEL_VERSION = "heuristic-v3"


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

def generate_recommendation(
    listing: "Listing",
    db: Session,
    use_vision: bool = False,
) -> dict:
    """
    Score a listing and return a dict suitable for AIRecommendation fields.
    reasoning is stored as a JSON array: [{"label": str, "delta": int|None}, ...]
    The first element is always the summary header with delta=None.
    """
    score, factors = _score_listing(listing)
    tier, recommendation = _get_tier(score)

    estimated_value   = _estimate_value(listing, score)
    suggested_max_bid = round(estimated_value * 0.35, 0) if estimated_value else None

    summary = {"label": f"Score {score}/100 · Tier {tier}", "delta": None}
    reasoning_json = json.dumps([summary] + factors)

    return {
        "recommendation":    recommendation,
        "confidence_score":  round(score / 100, 3),
        "estimated_value":   estimated_value,
        "suggested_max_bid": suggested_max_bid,
        "reasoning":         reasoning_json,
        "model_version":     MODEL_VERSION,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Tier mapping
# ─────────────────────────────────────────────────────────────────────────────

def _get_tier(score: int) -> tuple:
    if score >= 85: return ("A+", "buy")
    if score >= 70: return ("A",  "buy")
    if score >= 55: return ("B",  "watch")
    if score >= 40: return ("C",  "risky")
    return ("D", "skip")


# ─────────────────────────────────────────────────────────────────────────────
# Main scoring function
# ─────────────────────────────────────────────────────────────────────────────

def _score_listing(listing: "Listing") -> tuple:
    """Return (score 0-100, list of {label, delta} factor dicts)."""
    score: int   = 0
    factors: list = []

    def add(label: str, delta: int) -> None:
        nonlocal score
        score += delta
        factors.append({"label": label, "delta": delta})

    # ── 1. Auction type ───────────────────────────────────────────────────
    atype = (listing.auction_type or "").lower()
    if "lien" in atype:
        add("Lien unit", 15)
    elif "manager" in atype:
        add("Manager special", 5)
    elif "charity" in atype:
        add("Charity unit", -5)
    # private seller / unknown = 0 pts

    # ── 2. Unit size ──────────────────────────────────────────────────────
    size_norm = (listing.unit_size or "").lower().replace(" ", "")
    if "10x20" in size_norm or "20x10" in size_norm:
        add("10×20 unit", 20)
    elif "10x15" in size_norm or "15x10" in size_norm:
        add("10×15 unit", 18)
    elif "10x10" in size_norm:
        add("10×10 unit", 15)
    elif "5x10" in size_norm or "10x5" in size_norm:
        add("5×10 unit", 8)
    elif "5x5" in size_norm:
        add("5×5 unit", 2)

    # ── 3. Current bid ────────────────────────────────────────────────────
    bid = listing.current_bid or 0.0
    if bid < 100:
        add(f"Bid under $100 (${bid:.0f})", 15)
    elif bid <= 200:
        add(f"Bid $100–200 (${bid:.0f})", 10)
    elif bid <= 400:
        add(f"Bid $200–400 (${bid:.0f})", 5)
    else:
        add(f"Bid over $400 (${bid:.0f})", -10)

    # ── 4. Bid count ──────────────────────────────────────────────────────
    n_bids = listing.bid_count or 0
    if n_bids <= 5:
        add(f"{n_bids} bids — low competition", 10)
    elif n_bids <= 15:
        add(f"{n_bids} bids — moderate competition", 5)
    elif n_bids <= 25:
        pass  # neutral, no note
    else:
        add(f"{n_bids} bids — high competition", -10)

    # ── 5. Time remaining ─────────────────────────────────────────────────
    if listing.auction_end_time:
        now   = datetime.utcnow()
        delta = listing.auction_end_time - now
        hours = delta.total_seconds() / 3600
        if hours > 24:
            add("Over 24 hrs remaining", 5)
        elif hours > 6:
            add("6–24 hrs remaining", 3)
        else:
            add("Under 6 hrs remaining", -5)

    # ── 6. Description keyword analysis ──────────────────────────────────
    desc = (listing.description or "").lower()

    if not desc.strip():
        add("No description", -5)
    else:
        if any(w in desc for w in ["tools", "toolbox", "dewalt", "milwaukee", "craftsman"]):
            add("Tools / branded tools", 15)
        if any(w in desc for w in ["electronics", "tv", "laptop", "gaming"]):
            add("Electronics mentioned", 10)
        if any(w in desc for w in ["boxes", "sealed", "retail"]):
            add("Boxes / sealed / retail", 10)
        if any(w in desc for w in ["furniture", "dresser", "couch"]):
            add("Furniture mentioned", 5)
        if "mattress" in desc:
            add("Mattress mentioned", -15)
        if any(w in desc for w in ["clothes", "clothing"]):
            add("Clothing", -10)
        if any(w in desc for w in ["trash", "junk", "empty"]):
            add("Trash / junk / empty", -20)
        if any(w in desc for w in ["water", "damage"]):
            add("Water / damage mentioned", -15)

    # ── 7. Images ────────────────────────────────────────────────────────
    if not listing.images:
        add("No images", -10)

    score = max(0, min(100, score))
    return score, factors


# ─────────────────────────────────────────────────────────────────────────────
# Value estimation
# ─────────────────────────────────────────────────────────────────────────────

def _estimate_value(listing: "Listing", score: int) -> Optional[float]:
    """Rough resale value estimate based on unit size and score."""
    size_sqft = listing.unit_size_sqft or _parse_size_sqft(listing.unit_size) or 0.0
    base = max(size_sqft * 3.0, 50.0)   # $3/sqft, minimum $50
    # Score multiplier: 0.4× for terrible units, 1.6× for A+ units
    multiplier = 0.4 + (score / 100.0) * 1.2
    return round(base * multiplier, 0)


# ─────────────────────────────────────────────────────────────────────────────
# Utilities
# ─────────────────────────────────────────────────────────────────────────────

def _parse_size_sqft(size_str: Optional[str]) -> Optional[float]:
    """Parse '10x10' or '5 x 10' style strings to square footage."""
    if not size_str:
        return None
    parts = size_str.lower().replace(" ", "").split("x")
    if len(parts) == 2:
        try:
            return float(parts[0]) * float(parts[1])
        except ValueError:
            pass
    return None
