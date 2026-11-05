"""Export all bmSticker entries from Contentful to data/stickers.json (read only)."""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

CONTENT_TYPE = "bmSticker"
PAGE_SIZE = 1000
OUTPUT_PATH = Path("data/stickers.json")


def load_config():
    """Read the three Contentful values from .env; never echo their values."""
    load_dotenv()
    keys = [
        "CONTENTFUL_SPACE_ID",
        "CONTENTFUL_ENVIRONMENT_ID",
        "CONTENTFUL_DELIVERY_TOKEN",
    ]
    missing = [key for key in keys if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing in .env: {', '.join(missing)}")
    space, environment, token = (os.environ[key] for key in keys)
    url = (
        f"https://cdn.contentful.com/spaces/{space}"
        f"/environments/{environment}/entries"
    )
    # Token travels in a header, so it never appears in a URL or error text.
    headers = {"Authorization": f"Bearer {token}"}
    return url, headers


def fetch_all(url, headers):
    """Page through every bmSticker entry; return (entries, assets_by_id)."""
    entries = []
    assets = {}
    skip = 0
    while True:
        params = {
            "content_type": CONTENT_TYPE,
            "limit": PAGE_SIZE,
            "skip": skip,
            "order": "sys.id",
        }
        response = requests.get(url, headers=headers, params=params, timeout=30)
        if not response.ok:
            raise RuntimeError(
                f"Contentful request failed: HTTP {response.status_code}"
            )
        data = response.json()
        items = data.get("items", [])
        if not items:
            break
        entries.extend(items)
        for asset in data.get("includes", {}).get("Asset", []):
            assets[asset["sys"]["id"]] = asset
        skip += len(items)
    return entries, assets


def rich_text_to_text(node):
    """Flatten a Contentful Rich Text node to plain text."""
    if node.get("nodeType") == "text":
        return node.get("value", "")
    parts = [rich_text_to_text(child) for child in node.get("content", [])]
    # Block nodes (document, paragraph, list...) get a newline between children.
    return "\n".join(parts) if node.get("nodeType") == "document" else "".join(parts)


KEPT_FIELDS = [
    "title",
    "slug",
    "year",
    "officialTheme",
    "bmTheme",
    "shape",
    "themeCampName",
    "campLink",
    "artProjectName",
    "artProjectLink",
    "artCarName",
    "artCarLink",
    "officialSticker",
    "featuredSticker",
    "createdBy",
    "creatorInfo",
    "contributor",
    "imageAlt",
]


def blank_to_none(value):
    """Turn empty or whitespace-only strings into None; leave everything else."""
    if isinstance(value, str) and not value.strip():
        return None
    return value


def simplify(entry, assets):
    """Return (record, used_fallback) for one entry."""
    fields = entry["fields"]
    slug = blank_to_none(fields.get("slug"))
    used_fallback = slug is None
    record = {"id": slug or entry["sys"]["id"]}
    for key in KEPT_FIELDS:
        record[key] = fields.get(key)

    description = fields.get("description")
    record["description"] = rich_text_to_text(description) if description else None

    image_id = fields.get("image", {}).get("sys", {}).get("id")
    file_url = assets.get(image_id, {}).get("fields", {}).get("file", {}).get("url")
    record["imageUrl"] = f"https:{file_url}" if file_url else None
    return {key: blank_to_none(value) for key, value in record.items()}, used_fallback


def fetch_stickers():
    """Fetch every sticker from Contentful and return the simplified records.

    Safe to call from the MCP server: it never prints and never exits.
    It raises RuntimeError with a clear message if something goes wrong.
    """
    url, headers = load_config()
    entries, assets = fetch_all(url, headers)
    return [simplify(entry, assets)[0] for entry in entries]


def main():
    try:
        stickers = fetch_stickers()
    except RuntimeError as error:
        sys.exit(str(error))

    # A sticker with no slug has slug None, and simplify() gave it its sys.id.
    fallback_count = sum(1 for sticker in stickers if sticker["slug"] is None)

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(stickers, f, indent=2, ensure_ascii=False)

    print(f"{fallback_count} stickers used sys.id as id (no slug)")
    print(f"Saved {len(stickers)} stickers to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
