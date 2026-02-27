# storage-scraper — Feature Roadmap

## Phase 1 — Foundation (complete)
- [x] SQLAlchemy models: Listing, Image, Tag, BidRecord, PnLEntry, InventoryItem, AIRecommendation
- [x] FastAPI app with all 5 router modules
- [x] StorageTreasures scraper skeleton (httpx + Playwright hybrid)
- [x] Heuristic AI recommender (rule-based scoring)
- [x] P&L CRUD + summary endpoint
- [x] Fixed route ordering bug (/summary vs /{pnl_id})
- [x] Fixed trailing slash 404 on /api/pnl/
- [x] Filter ended auctions from scrape results
- [x] Filter ended listings from API response

## Phase 2 — Dashboard UI (complete)
- [x] HTML/CSS/JS dashboard at `app/dashboard/static/`
- [x] Listings grid view with AI recommendation badges
- [x] Unit detail page with images, tags, bid form
- [x] P&L table with chart (win/loss over time)
- [x] Analysis charts (by tag, by size)
- [x] Auction type badge on listing cards
- [x] Auction type filter checkboxes (Lien, Manager Special, Private Seller, Charity)
- [x] Zip code + radius distance filter with Apply button (filters but not yet sorting)

## Phase 3 — Scraper Hardening (in progress)
- [x] Parse auction end time from StorageTreasures API
- [x] Filter out ended auctions during scrape
- [x] Playwright fallback for JS-rendered content
- [x] Scrape by FL state to get all listings
- [ ] Fix distance filter sorting (sort by distance after coords resolve)
- [ ] Fix cascade delete on ai_recommendations (add to models.py)
- [ ] Add pgeocode to requirements.txt
- [ ] Fetch full listing detail page (all images)
- [ ] Scheduled scraping (APScheduler or cron)
- [ ] HTML fixture tests for parser resilience

## Phase 4 — ML Model
- [ ] Feature engineering from Listing + PnLEntry history
- [ ] Train scikit-learn RandomForestClassifier/Regressor
- [ ] Cross-validation and model persistence (joblib)
- [ ] Model versioning and A/B comparison

## Phase 5 — LLM Integration
- [ ] Image analysis via Claude API (describe unit contents)
- [ ] Description NLP feature extraction
- [ ] Auto-tagging from images + description
- [ ] Confidence calibration

## Phase 6 — CSV Import/Export
- [ ] Import inventory from CSV (InventoryItem bulk create)
- [ ] Export P&L to Excel/CSV for taxes
- [ ] Import historical auction data for cold-start ML training
