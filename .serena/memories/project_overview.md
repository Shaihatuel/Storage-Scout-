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
- **Zip distance**: pgeocode library (local, no API calls) for instant zip code distance calculations

## Repo
- GitHub: https://github.com/Shaihatuel/Storage-Scout-
- Local: `/Users/shaihatuel/storage-scraper`

## Fixes Applied (Feb 2026)
- `launch.command`: fixed localhost→127.0.0.1, added venv check, PID file, health poll
- `pnl.py`: moved /summary route above /{pnl_id} to prevent FastAPI route conflict
- `index.html`: removed trailing slash from /api/pnl/ call causing 404
- `storage_treasures.py`: skip ended auctions during scrape (end_time < utcnow)
- `listings.py`: filter ended listings from API response (auction_end_time > utcnow)
- `listings.py`: added auction_type to API response
- `index.html`: added auction type badge on listing cards
- `index.html`: added auction type filter checkboxes (Lien, Manager Special, Private Seller, Charity)
- `index.html`: added zip code + radius distance filter with Apply button
- `storage_treasures.py`: removed per-listing distance filter, scrape FL by state instead
- `data/*.db`: added to .gitignore

## Known Issues / TODO (as of Feb 2026)
- **Distance filter not sorting**: zip+radius Apply button filters but does NOT sort listings by distance. Need to sort S.filtered by distance from entered zip after applyFilters() runs. Uses zippopotam.us async fetch for coords — coords may not be cached yet on first Apply click, causing filter to pass everything through. Fix: pre-fetch all listing zip coords when zip is entered, or sort after coords resolve.
- **Cascade delete missing**: deleting a Listing does not cascade to ai_recommendations due to missing cascade on the ORM relationship. Must manually delete child records first. Fix: add cascade="all, delete-orphan" to Listing.ai_recommendation relationship in models.py.
- **pgeocode installed in system Python**: pgeocode was installed with --break-system-packages, should be added to requirements.txt so it installs in venv properly.
