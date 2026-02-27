# Architecture

## Directory layout
cat > ~/storage-scraper/.serena/memories/architecture.md << 'EOF'
# Architecture

## Directory layout
```
storage-scraper/
  app/
    main.py            — FastAPI app, lifespan, router registration
    models.py          — all ORM models
    database.py        — engine, init_db(), get_db(), _migrate()
    api/
      listings.py      — listings CRUD + watch/bid/notes/status toggles
      bidding.py       — bid records
      pnl.py           — P&L entries (/summary must be above /{pnl_id})
      analysis.py      — win/loss analysis
      ai.py            — AI recommendation endpoints
      scraper.py       — POST /api/scraper/run (sync, blocking)
    ai/
      recommender.py   — heuristic-v3 scoring, generate_recommendation()
      image_analyzer.py— Claude Vision image analysis (optional)
    scraper/
      storage_treasures.py — Playwright+httpx hybrid scraper
    dashboard/
      static/index.html — single-file SPA dashboard
  data/
    storage_scraper.db — SQLite database
  launch.command       — Mac launcher (uvicorn on 127.0.0.1:8000)
```

## Models
- **Listing**: id, external_id, url, facility_name/address, city, state, zip_code, unit_number, unit_size, unit_size_sqft, description, **notes**, auction_end_time, auction_type, **watched**, current_bid, bid_count, status, scraped_at, updated_at
- **ListingImage**: id, listing_id, url, local_path, order_index, downloaded_at
- **ListingTagMap**: id, listing_id, tag (UnitTag enum), confidence, source
- **BidRecord**: id, listing_id, max_bid, actual_bid, winning_bid, did_win, notes, decision_at
- **PnLEntry**: id, listing_id, purchase_price, cleanup/transport/other costs, gross_revenue, net_profit, notes, closed_at
- **InventoryItem**: id, pnl_entry_id, name, category, quantity, estimated_value, sold_price, sold_at, platform, notes
- **AIRecommendation**: id, listing_id, recommendation, confidence_score, estimated_value, suggested_max_bid, reasoning (JSON array), model_version, generated_at

## Enums
- AuctionStatus: active, won, lost, skipped
- UnitTag: furniture, electronics, tools, clothing, boxes, appliances, vehicles, collectibles, mixed, junk

## AI scoring (heuristic-v3)
- Additive from 0; tiers A+(85+/buy), A(70-84/buy), B(55-69/watch), C(40-54/risky), D(<40/skip)
- reasoning stored as JSON: [{label, delta|None}, ...] — first item is summary header (delta=None)
- generate_recommendation() returns dict with reasoning as json.dumps([summary] + factors)

## DB migrations
database._migrate() handles additive column migrations:
- listings.auction_type (VARCHAR)
- listings.watched (BOOLEAN DEFAULT 0)
- listings.notes (TEXT)

## Scraper
- StorageTreasuresScraper.fetch_and_save() returns (new_count, total_fetched)
- Playwright for page 1 auth + header capture; httpx for pages 2+
- auction_type captured from API numeric field (1=lien, 2=private, 3=manager_special, 4=charity)
- Ended auctions filtered out in _upsert(): if end_time < datetime.utcnow() → return False

## Known Bugs Fixed (Feb 2026)
- pnl.py: /summary route must be declared BEFORE /{pnl_id} or FastAPI matches summary as an ID
- index.html: frontend was calling /api/pnl/ (trailing slash) → 404; fixed to /api/pnl
- launch.command: use 127.0.0.1 consistently (not localhost); added venv check, PID file, health poll
- storage_treasures.py: skip auctions where end_time < utcnow during _upsert

## Route registration rule
Always use @router.get("") not @router.get("/") for collection endpoints.
StaticFiles mount at "/" intercepts trailing-slash redirects → 404.
Applied to: listings.py, bidding.py, pnl.py, analysis.py
