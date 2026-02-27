"""
StorageTreasures.com scraper.

Strategy:
  - Page 1: Playwright browser (handles all auth/cookies automatically).
            Intercepts the API response JSON directly.
            Also captures the raw request headers for reuse.
  - Pages 2+: httpx using the same headers captured from Playwright.
              Falls back to a second Playwright pass if httpx gets a 403.

The site's data API:
  GET https://api.st-prd-1.aws.storagetreasures.com/p/auctions
  Response: { "auctions": [...], "total_records": N }

Image CDN:
  https://media.st-prd-1.aws.storagetreasures.com/data/auctions/images/
    {digit}/{digit}/.../thumb.jpg  (image_id split into single digits)
"""
from __future__ import annotations

import asyncio
import logging
import random
import string
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import httpx
from sqlalchemy.orm import Session

from app.models import Listing, ListingImage
from app.database import SessionLocal

logger = logging.getLogger(__name__)

API_URL  = "https://api.st-prd-1.aws.storagetreasures.com/p/auctions"
SITE_URL = "https://www.storagetreasures.com"

IMAGE_DIR = Path(__file__).parent.parent.parent / "data" / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _rand(n: int = 12) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


# ─────────────────────────────────────────────────────────────────────────────
# Public interface
# ─────────────────────────────────────────────────────────────────────────────

class StorageTreasuresScraper:
    """
    Scrapes StorageTreasures.com auction listings and saves them to the DB.

    Usage (synchronous, from CLI / tests):
        scraper = StorageTreasuresScraper()
        count = scraper.fetch_and_save(state="FL", max_pages=2)
        print(f"{count} new listings saved")
    """

    def __init__(self, headless: bool = True, delay: float = 1.5):
        self.headless = headless
        self.delay    = delay         # seconds between paginated httpx requests

    # ------------------------------------------------------------------
    # Sync wrapper (runs the async implementation)
    # ------------------------------------------------------------------
    def fetch_and_save(
        self,
        state:        Optional[str] = None,
        zip_code:     Optional[str] = None,
        radius_miles: int           = 50,
        max_pages:    int           = 5,
        filter_types: str           = "1,2,3,4",
        db:           Optional[Session] = None,
    ) -> tuple:
        """Fetch listings and upsert to DB.  Returns (new_count, total_fetched)."""
        return asyncio.run(
            self._fetch_and_save_async(state, zip_code, radius_miles, max_pages, filter_types, db)
        )

    # ------------------------------------------------------------------
    # Internal async implementation
    # ------------------------------------------------------------------
    async def _fetch_and_save_async(
        self,
        state:        Optional[str],
        zip_code:     Optional[str],
        radius_miles: int,
        max_pages:    int,
        filter_types: str,
        db:           Optional[Session],
    ) -> tuple:
        close_db = db is None
        if db is None:
            db = SessionLocal()
        try:
            auctions = await self._fetch_all_pages(state, zip_code, radius_miles, max_pages, filter_types)
            new_count = 0
            for a in auctions:
                if self._upsert(a, db):
                    new_count += 1
            db.commit()
            logger.info(f"Scrape complete: {new_count} new / {len(auctions)} total fetched")
            return new_count, len(auctions)
        finally:
            if close_db:
                db.close()

    async def _fetch_all_pages(
        self,
        state:        Optional[str],
        zip_code:     Optional[str],
        radius_miles: int,
        max_pages:    int,
        filter_types: str = "1,2,3,4",
    ) -> List[dict]:
        """
        Fetch up to max_pages of results.
        Page 1 via Playwright (auth handled automatically).
        Pages 2+ via httpx with captured headers.
        """
        from playwright.async_api import async_playwright

        page1_auctions: List[dict] = []
        captured_headers: dict     = {}
        total_records: int         = 0

        # ── PLAYWRIGHT: page 1 ────────────────────────────────────────
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            ctx = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )
            page = await ctx.new_page()

            # Capture request headers so we can replay them with httpx
            def on_request(req: object) -> None:
                if API_URL in req.url and "upcoming" not in req.url:
                    captured_headers.update(req.headers)

            page1_body: dict = {}

            async def on_response(resp: object) -> None:
                nonlocal page1_body
                url: str = resp.url
                if API_URL in url and "upcoming" not in url:
                    try:
                        body = await resp.json()
                        # Use the response that actually contains state-filtered data
                        if body.get("auctions") and not page1_body.get("auctions"):
                            page1_body = body
                    except Exception as exc:
                        logger.debug(f"Response parse error: {exc}")

            page.on("request",  on_request)
            page.on("response", on_response)

            search_url = f"{SITE_URL}/auctions"
            if state:
                search_url += f"?state={state}"
            elif zip_code:
                search_url += f"?type=zipcode&radius={radius_miles}&search_term={zip_code}"

            logger.info(f"Playwright → {search_url}")
            await page.goto(search_url, wait_until="networkidle", timeout=45000)
            await browser.close()

        page1_auctions = page1_body.get("auctions", [])
        total_records  = int(page1_body.get("total_records", 0))
        logger.info(
            f"Page 1: {len(page1_auctions)} auctions  "
            f"(total_records={total_records})"
        )

        all_auctions = list(page1_auctions)

        if max_pages <= 1 or not captured_headers:
            return all_auctions

        # ── HTTPX: pages 2 .. max_pages ───────────────────────────────
        search_type = "state"   if state    else "zipcode"
        search_term = state     if state    else (zip_code or "")

        with httpx.Client(timeout=20) as client:
            for page_num in range(2, max_pages + 1):
                if not all_auctions and page_num > 1:
                    break  # nothing on previous page → stop

                time.sleep(self.delay)

                params: dict = {
                    "page_num":          page_num,
                    "page_count":        15,
                    "search_type":       search_type,
                    "search_term":       search_term,
                    "filter_types":      filter_types,
                    "filter_categories": "",
                    "filter_unit_contents": "",
                    "sort_column":       "expire_date",
                    "sort_direction":    "asc",
                    "filter_public_notice": "",
                    "randStr":           _rand(),
                }
                if state:
                    params["search_state"] = state

                try:
                    resp = client.get(API_URL, headers=captured_headers, params=params)
                    resp.raise_for_status()
                    data     = resp.json()
                    page_aus = data.get("auctions", [])
                    logger.info(f"Page {page_num}: {len(page_aus)} auctions")
                    all_auctions.extend(page_aus)
                    if not page_aus:
                        break
                except httpx.HTTPStatusError as exc:
                    logger.warning(
                        f"Page {page_num} returned {exc.response.status_code} "
                        f"— stopping pagination"
                    )
                    break
                except Exception as exc:
                    logger.error(f"Page {page_num} error: {exc}")
                    break

        return all_auctions

    # ------------------------------------------------------------------
    # DB upsert
    # ------------------------------------------------------------------
    def _upsert(self, a: dict, db: Session) -> bool:
        """Insert or update one auction.  Returns True if NEW row was created."""
        external_id = str(a.get("auction_id", "")).strip()
        if not external_id:
            return False

        # ── Dates ──────────────────────────────────────────────────────
        expire_utc = (
            a.get("expire_date", {})
             .get("utc", {})
             .get("datetime")
        )
        end_time: Optional[datetime] = None
        if expire_utc:
            try:
                end_time = datetime.strptime(expire_utc, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        # ── Money ─────────────────────────────────────────────────────
        bid_raw = a.get("current_bid", {})
        current_bid: Optional[float] = (
            float(bid_raw["amount"])
            if isinstance(bid_raw, dict) and bid_raw.get("amount") is not None
            else None
        )

        # ── Skip ended auctions ───────────────────────────────────────
        if end_time and end_time < datetime.utcnow():
            return False

        # ── Existing → update only live fields ────────────────────────
        existing = (
            db.query(Listing)
            .filter(Listing.external_id == external_id)
            .first()
        )
        if existing:
            existing.current_bid = current_bid
            existing.bid_count   = int(a.get("total_bids") or 0)
            return False

        # ── Build listing URL ─────────────────────────────────────────
        state_slug = (a.get("state") or "").lower()
        city_slug  = (a.get("city")  or "").lower().replace(" ", "-")
        url = f"{SITE_URL}/auctions/{state_slug}/{city_slug}/{external_id}"

        # ── Description ───────────────────────────────────────────────
        description = "\n\n".join(
            filter(None, [a.get("unit_contents"), a.get("unit_additional")])
        ) or None

        # ── Unit size ─────────────────────────────────────────────────
        unit_size_sqft: Optional[float] = None
        vol = a.get("unit_volume")
        if vol:
            try:
                unit_size_sqft = float(vol)
            except (ValueError, TypeError):
                pass

        # ── Facility ──────────────────────────────────────────────────
        facility = a.get("facility") or {}
        facility_name = (
            a.get("facility_name")
            or facility.get("facility_name")
            or None
        )
        facility_address = (
            a.get("address")
            or facility.get("address")
            or None
        )

        # ── Auction type ───────────────────────────────────────────
        _TYPE_MAP = {1: "lien", 2: "private", 3: "manager_special", 4: "charity"}
        raw_type = a.get("type") or a.get("auction_type_id") or a.get("auction_type")
        try:
            auction_type = _TYPE_MAP.get(int(raw_type)) if raw_type is not None else None
        except (ValueError, TypeError):
            auction_type = str(raw_type).lower() if raw_type else None

        listing = Listing(
            external_id      = external_id,
            url              = url,
            facility_name    = facility_name,
            facility_address = facility_address,
            city             = a.get("city"),
            state            = a.get("state"),
            zip_code         = a.get("zipcode"),
            unit_number      = str(a.get("unit_number") or ""),
            unit_size        = a.get("unit_size"),
            unit_size_sqft   = unit_size_sqft,
            description      = description,
            auction_end_time = end_time,
            auction_type     = auction_type,
            current_bid      = current_bid,
            bid_count        = int(a.get("total_bids") or 0),
        )
        db.add(listing)
        db.flush()  # populate listing.id before adding images

        # ── Image ─────────────────────────────────────────────────────
        img = a.get("image") or {}
        thumb = img.get("image_path")
        if thumb:
            db.add(ListingImage(
                listing_id  = listing.id,
                url         = thumb,
                order_index = 0,
            ))

        return True

    # ------------------------------------------------------------------
    # Image download (optional post-scrape step)
    # ------------------------------------------------------------------
    def download_images(self, listing: Listing, db: Session) -> int:
        """Download listing photos to data/images/.  Returns count downloaded."""
        count = 0
        with httpx.Client(timeout=30) as client:
            for img in listing.images:
                if img.local_path:
                    continue
                try:
                    r   = client.get(img.url)
                    r.raise_for_status()
                    ext  = img.url.rsplit(".", 1)[-1].split("?")[0][:4]
                    path = IMAGE_DIR / f"{listing.external_id}_{img.order_index}.{ext}"
                    path.write_bytes(r.content)
                    img.local_path    = str(path)
                    img.downloaded_at = datetime.utcnow()
                    count += 1
                    time.sleep(0.3)
                except Exception as exc:
                    logger.warning(f"Image download failed ({img.url}): {exc}")
        db.commit()
        return count
