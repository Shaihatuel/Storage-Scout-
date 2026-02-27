# StorageTreasures Scraper — Technical Details

## API Endpoint (discovered via Playwright network intercept)
GET https://api.st-prd-1.aws.storagetreasures.com/p/auctions

## Key Parameters
- page_num, page_count (15 per page, 2180 total FL records as of Feb 2026)
- search_type: "state" | "zipcode"
- search_term: "FL" (state code) or zip string
- search_state: "FL"
- filter_types: "1,2,3,4"
- sort_column: "expire_date", sort_direction: "asc"
- randStr: random 12-char string (cache busting)

## Auth / Access
- Direct httpx calls return 403 — requires browser cookies/tokens
- Strategy: Page 1 via Playwright (handles auth automatically), intercept response JSON
- Pages 2+: httpx using captured request headers from Playwright (works with 200)
- Image CDN: https://media.st-prd-1.aws.storagetreasures.com/data/auctions/images/{digit}/{digit}.../thumb.jpg

## Key JSON Fields
- auction_id, unit_number, unit_width, unit_length, unit_size, unit_volume (sqft)
- unit_contents (description), unit_additional
- facility_name, address, city, state, zipcode
- current_bid: {amount: float, formatted: "$N"}
- total_bids, expire_date.utc.datetime
- image: {image_path, image_path_large, image_path_giant}
- total_records (pagination total)

## 404 Fix (applied)
`@router.get("/")` with prefix `/api/listings` registers route as `/api/listings/`
StaticFiles mount at "/" intercepts the redirect → 404
Fix: use `@router.get("")` (empty string) for all collection endpoints
Applied to: listings.py, bidding.py, pnl.py
