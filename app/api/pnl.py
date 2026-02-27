"""
API routes for P&L tracking and inventory management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.database import get_db
from app.models import PnLEntry, InventoryItem

router = APIRouter()


class PnLCreate(BaseModel):
    listing_id: int
    purchase_price: float
    cleanup_cost: float = 0.0
    transport_cost: float = 0.0
    other_costs: float = 0.0
    notes: Optional[str] = None


class PnLUpdate(BaseModel):
    cleanup_cost: Optional[float] = None
    transport_cost: Optional[float] = None
    other_costs: Optional[float] = None
    gross_revenue: Optional[float] = None
    notes: Optional[str] = None
    closed_at: Optional[datetime] = None


class InventoryItemCreate(BaseModel):
    name: str
    category: Optional[str] = None
    quantity: int = 1
    estimated_value: Optional[float] = None
    sold_price: Optional[float] = None
    sold_at: Optional[datetime] = None
    platform: Optional[str] = None
    notes: Optional[str] = None


def _compute_net(entry: PnLEntry) -> float:
    total_cost = (entry.purchase_price + entry.cleanup_cost +
                  entry.transport_cost + entry.other_costs)
    return (entry.gross_revenue or 0.0) - total_cost


@router.get("")
def list_pnl(db: Session = Depends(get_db)):
    entries = db.query(PnLEntry).all()
    return [_pnl_dict(e) for e in entries]


@router.get("/summary")
def pnl_summary(db: Session = Depends(get_db)):
    entries = db.query(PnLEntry).all()
    total_invested = sum(
        (e.purchase_price + e.cleanup_cost + e.transport_cost + e.other_costs)
        for e in entries
    )
    total_revenue = sum(e.gross_revenue or 0.0 for e in entries)
    total_net = sum(e.net_profit or 0.0 for e in entries)
    wins = [e for e in entries if (e.net_profit or 0) > 0]
    losses = [e for e in entries if (e.net_profit or 0) <= 0]
    return {
        "total_units": len(entries),
        "total_invested": round(total_invested, 2),
        "total_revenue": round(total_revenue, 2),
        "total_net_profit": round(total_net, 2),
        "win_count": len(wins),
        "loss_count": len(losses),
        "win_rate": round(len(wins) / len(entries), 3) if entries else 0,
        "avg_net_per_unit": round(total_net / len(entries), 2) if entries else 0,
    }


@router.post("")
def create_pnl(data: PnLCreate, db: Session = Depends(get_db)):
    entry = PnLEntry(**data.model_dump())
    entry.net_profit = _compute_net(entry)
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _pnl_dict(entry)


@router.patch("/{pnl_id}")
def update_pnl(pnl_id: int, data: PnLUpdate, db: Session = Depends(get_db)):
    entry = db.get(PnLEntry, pnl_id)
    if not entry:
        raise HTTPException(404, "P&L entry not found")
    for field, val in data.model_dump(exclude_none=True).items():
        setattr(entry, field, val)
    entry.net_profit = _compute_net(entry)
    db.commit()
    db.refresh(entry)
    return _pnl_dict(entry)


@router.post("/{pnl_id}/inventory")
def add_inventory_item(pnl_id: int, item: InventoryItemCreate, db: Session = Depends(get_db)):
    entry = db.get(PnLEntry, pnl_id)
    if not entry:
        raise HTTPException(404, "P&L entry not found")
    inv = InventoryItem(pnl_entry_id=pnl_id, **item.model_dump())
    db.add(inv)
    entry.gross_revenue = (entry.gross_revenue or 0) + (item.sold_price or 0)
    entry.net_profit = _compute_net(entry)
    db.commit()
    db.refresh(inv)
    return {"id": inv.id, "name": inv.name, "sold_price": inv.sold_price}


def _pnl_dict(entry: PnLEntry) -> dict:
    total_cost = (entry.purchase_price + entry.cleanup_cost +
                  entry.transport_cost + entry.other_costs)
    return {
        "id": entry.id,
        "listing_id": entry.listing_id,
        "purchase_price": entry.purchase_price,
        "cleanup_cost": entry.cleanup_cost,
        "transport_cost": entry.transport_cost,
        "other_costs": entry.other_costs,
        "total_cost": round(total_cost, 2),
        "gross_revenue": entry.gross_revenue,
        "net_profit": entry.net_profit,
        "notes": entry.notes,
        "closed_at": entry.closed_at.isoformat() if entry.closed_at else None,
        "inventory_count": len(entry.inventory_items),
    }
