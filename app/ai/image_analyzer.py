"""
Claude Vision image analyzer for storage unit listings.

Sends the primary listing image to Claude and extracts structured signals
useful for the buy/skip/watch scoring model:
  - Content type signals (tools, electronics, retail inventory, etc.)
  - Risk flags (water damage, mattresses, heavy furniture)
  - Organization quality (neat / moderate / chaotic)
  - Visible brand names
"""
from __future__ import annotations

import base64
import json
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

VISION_MODEL = "claude-sonnet-4-6"

_SYSTEM = (
    "You are an expert storage unit resale analyst. "
    "A buyer resells items on eBay and Facebook Marketplace. "
    "Analyze storage unit images and return ONLY valid JSON with no other text."
)

_PROMPT = """\
Analyze this storage unit auction photo. Return a single JSON object with exactly these fields:

{
  "tools": <bool>,
  "electronics": <bool>,
  "furniture_heavy": <bool>,
  "mattress_visible": <bool>,
  "water_damage": <bool>,
  "organization_level": <"neat"|"moderate"|"chaotic">,
  "sealed_boxes": <bool>,
  "retail_inventory": <bool>,
  "contractor_unit": <bool>,
  "brand_names": [<string>, ...],
  "risk_flags": [<string>, ...],
  "notes": <string>
}

Definitions:
- tools: power/hand tools, drill, saw, compressor, workbench or similar
- electronics: TVs, computers, stereos, monitors, tablets, audio equipment
- furniture_heavy: large, hard-to-move pieces (couches, sectionals, heavy dressers, armoires)
- mattress_visible: any mattress or box spring
- water_damage: visible stains, mold, wet cardboard, musty discoloration
- organization_level: neat = bins/shelving/totes stacked; moderate = some order; chaotic = dumped/random pile
- sealed_boxes: sealed cardboard boxes (branded or plain)
- retail_inventory: uniform boxes, store overstock, merchandise on pallets
- contractor_unit: construction materials, contractor tools, job-site equipment
- brand_names: any legible brand/product names visible
- risk_flags: specific concerns (e.g. "visible mold on ceiling", "broken glass", "hazardous materials")
- notes: one brief sentence describing the unit overall
"""


def analyze_listing_images(image_urls: list) -> Optional[dict]:
    """
    Analyze the primary listing image using Claude Vision.

    Args:
        image_urls: List of image URLs; only the first is analyzed.

    Returns:
        Structured dict of signals, or None on failure.
    """
    if not image_urls:
        return None

    url = image_urls[0]

    try:
        # Download image bytes
        with httpx.Client(timeout=20) as http:
            r = http.get(url)
            r.raise_for_status()
            image_bytes = r.content
            media_type = r.headers.get("content-type", "image/jpeg").split(";")[0].strip()
            if not media_type.startswith("image/"):
                media_type = "image/jpeg"

        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

        # Call Claude Vision (sync client)
        import anthropic  # imported here to keep startup fast when key not set
        client = anthropic.Anthropic()
        message = client.messages.create(
            model=VISION_MODEL,
            max_tokens=512,
            system=_SYSTEM,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": _PROMPT,
                        },
                    ],
                }
            ],
        )

        raw = message.content[0].text.strip()

        # Strip markdown fences if model wrapped response
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:].strip()

        signals = json.loads(raw)
        logger.info(f"Vision analysis complete: org={signals.get('organization_level')} url={url}")
        return signals

    except json.JSONDecodeError as exc:
        logger.warning(f"Vision response not valid JSON: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"Image analysis failed ({url}): {exc}")
        return None
