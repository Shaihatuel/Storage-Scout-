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
- **Scraping**: httpx + BeautifulSoup4; Playwright optional for JS pages
- **ML/AI**: scikit-learn (RandomForest phase 2), heuristic rules (phase 1)
- **Frontend**: Browser-based dashboard (static files served via FastAPI)
- **Data**: SQLite database at `data/storage_scraper.db`; images at `data/images/`

## Repo Root
`/Users/shaihatuel/storage-scraper`
