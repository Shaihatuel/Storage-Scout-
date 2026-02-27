"""
SQLAlchemy ORM models for storage-scraper.
All tables defined here; SQLite database used for persistence.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship, DeclarativeBase
import enum


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AuctionStatus(str, enum.Enum):
    active = "active"
    won = "won"
    lost = "lost"
    skipped = "skipped"


class UnitTag(str, enum.Enum):
    furniture = "furniture"
    electronics = "electronics"
    tools = "tools"
    clothing = "clothing"
    boxes = "boxes"
    appliances = "appliances"
    vehicles = "vehicles"
    collectibles = "collectibles"
    mixed = "mixed"
    junk = "junk"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------

class Listing(Base):
    """A storage unit auction listing scraped from StorageTreasures."""
    __tablename__ = "listings"

    id = Column(Integer, primary_key=True)
    external_id = Column(String, unique=True, nullable=False, index=True)
    url = Column(String, nullable=False)
    facility_name = Column(String)
    facility_address = Column(String)
    city = Column(String)
    state = Column(String)
    zip_code = Column(String)
    unit_number = Column(String)
    unit_size = Column(String)  # e.g. "10x10"
    unit_size_sqft = Column(Float)
    description = Column(Text)
    notes = Column(Text)
    auction_end_time = Column(DateTime)
    auction_type = Column(String)          # "lien" | "private" | "manager_special" | "charity"
    watched = Column(Boolean, default=False)
    current_bid = Column(Float)
    bid_count = Column(Integer, default=0)
    status = Column(Enum(AuctionStatus), default=AuctionStatus.active)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    images = relationship("ListingImage", back_populates="listing", cascade="all, delete-orphan")
    bid_record = relationship("BidRecord", back_populates="listing", uselist=False)
    pnl_entry = relationship("PnLEntry", back_populates="listing", uselist=False)
    tags = relationship("ListingTagMap", back_populates="listing", cascade="all, delete-orphan")
    ai_recommendation = relationship("AIRecommendation", back_populates="listing", uselist=False)


class ListingImage(Base):
    """Images associated with a listing."""
    __tablename__ = "listing_images"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    url = Column(String, nullable=False)
    local_path = Column(String)  # path to downloaded file
    order_index = Column(Integer, default=0)
    downloaded_at = Column(DateTime)

    listing = relationship("Listing", back_populates="images")


class ListingTagMap(Base):
    """Many-to-many: listing <-> UnitTag."""
    __tablename__ = "listing_tags"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    tag = Column(Enum(UnitTag), nullable=False)
    confidence = Column(Float, default=1.0)  # 0-1, manual=1.0
    source = Column(String, default="manual")  # "manual" | "ai"

    listing = relationship("Listing", back_populates="tags")


# ---------------------------------------------------------------------------
# Bidding
# ---------------------------------------------------------------------------

class BidRecord(Base):
    """Our bid decision and outcome for a listing."""
    __tablename__ = "bid_records"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, unique=True)
    max_bid = Column(Float)          # our max bid amount
    actual_bid = Column(Float)       # final bid placed
    winning_bid = Column(Float)      # final auction price
    did_win = Column(Boolean)
    notes = Column(Text)
    decision_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="bid_record")


# ---------------------------------------------------------------------------
# P&L
# ---------------------------------------------------------------------------

class PnLEntry(Base):
    """Profit and loss record for a won unit."""
    __tablename__ = "pnl_entries"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, unique=True)
    purchase_price = Column(Float, nullable=False)
    cleanup_cost = Column(Float, default=0.0)
    transport_cost = Column(Float, default=0.0)
    other_costs = Column(Float, default=0.0)
    gross_revenue = Column(Float, default=0.0)
    net_profit = Column(Float)       # computed: gross_revenue - total_costs
    notes = Column(Text)
    closed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    listing = relationship("Listing", back_populates="pnl_entry")
    inventory_items = relationship("InventoryItem", back_populates="pnl_entry", cascade="all, delete-orphan")


class InventoryItem(Base):
    """Individual items sold from a won unit."""
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True)
    pnl_entry_id = Column(Integer, ForeignKey("pnl_entries.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String)
    quantity = Column(Integer, default=1)
    estimated_value = Column(Float)
    sold_price = Column(Float)
    sold_at = Column(DateTime)
    platform = Column(String)  # eBay, Facebook Marketplace, etc.
    notes = Column(Text)

    pnl_entry = relationship("PnLEntry", back_populates="inventory_items")


# ---------------------------------------------------------------------------
# AI / Analysis
# ---------------------------------------------------------------------------

class AIRecommendation(Base):
    """AI buy/skip recommendation for a listing."""
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, unique=True)
    recommendation = Column(String)       # "buy" | "skip" | "watch"
    confidence_score = Column(Float)      # 0.0 – 1.0
    estimated_value = Column(Float)
    suggested_max_bid = Column(Float)
    reasoning = Column(Text)
    model_version = Column(String)
    generated_at = Column(DateTime, default=datetime.utcnow)

    listing = relationship("Listing", back_populates="ai_recommendation")
