# storage-scraper — Project Overview

## Purpose
Storage auction research, bidding assistant, and P&L tracking application.

## Five Core Features
1. **Scraper** — Scrapes StorageTreasures.com auction listings + images
2. **Bidding System** — Tag, evaluate, and track bid decisions per unit
3. **P&L Tracker** — Purchase price, costs, revenue, inventory items per won unit
4. **Pattern Analysis** — Win/loss patterns by tag, unit size, bid efficiency
5. **AI Recommendation Engine** — Learns from historical P&L; produces buy/skip/watch recommendations with confidence scores

## Tech Stack
- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2.x (ORM), SQLite
- **Scraping**: httpx + Playwright hybrid (Playwright for page 1 auth, httpx for pages 2+)
- **ML/AI**: scikit-learn (RandomForest phase 2), heuristic rules (phase 1)
- **Frontend**: Browser-based single-file SPA dashboard (static files served via FastAPI)
- **Data**: SQLite database at `data/storage_scraper.db`; images at `data/images/`
- **Launcher**: `launch.command` — Mac double-click launcher using uvicorn on 127.0.0.1:8000

## Repo
- GitHub: https://github.com/Shaihatuel/Storage-Scout-
- Local: `/Users/shaihatuel/storage-scraper`

## Known Fixes Applied (Feb 2026)
- `launch.command`: fixed localhost→127.0.0.1, added venv check, PID file, health poll replacing sleep 2
- `pnl.py`: moved `/summary` route above `/{pnl_id}` to prevent FastAPI route conflict
- `index.html`: removed trailing slash from `/api/pnl/` call causing 404
- `storage_treasures.py`: skip ended auctions during scrape (end_time < utcnow)
