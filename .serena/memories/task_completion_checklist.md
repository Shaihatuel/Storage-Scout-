# storage-scraper — Task Completion Checklist

After completing any coding task:

1. **Lint**: `ruff check app/ tests/`
2. **Format**: `ruff format app/ tests/`
3. **Tests**: `pytest tests/ -v`
4. **Manual smoke test** (if applicable): start server with `uvicorn app.main:app --reload` and hit /api/health
5. **DB schema changes**: if models.py changed, verify `init_db()` creates tables correctly
6. **Scraper changes**: test against a saved HTML fixture before hitting live site
7. **AI changes**: verify `generate_recommendation()` returns all required dict keys

## Key invariants to check
- `PnLEntry.net_profit` is always recomputed (not left stale) when any cost/revenue field changes
- `AIRecommendation.confidence_score` is always in [0.0, 1.0]
- `Listing.external_id` is unique — upsert logic must check before inserting
- Images are never re-downloaded if `local_path` is already set
