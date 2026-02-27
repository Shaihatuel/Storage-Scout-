# storage-scraper — Feature Roadmap

## Phase 1 — Foundation (current)
- [x] SQLAlchemy models: Listing, Image, Tag, BidRecord, PnLEntry, InventoryItem, AIRecommendation
- [x] FastAPI app with all 5 router modules
- [x] StorageTreasures scraper skeleton (httpx + BeautifulSoup)
- [x] Heuristic AI recommender (rule-based scoring)
- [x] P&L CRUD + summary endpoint

## Phase 2 — Dashboard UI
- [ ] HTML/CSS/JS dashboard at `app/dashboard/static/`
- [ ] Listings grid view with AI recommendation badges
- [ ] Unit detail page with images, tags, bid form
- [ ] P&L table with chart (win/loss over time)
- [ ] Analysis charts (by tag, by size)

## Phase 3 — Scraper Hardening
- [ ] Parse auction end time from StorageTreasures HTML
- [ ] Fetch full listing detail page (description, all images)
- [ ] Add Playwright fallback for JS-rendered content
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
