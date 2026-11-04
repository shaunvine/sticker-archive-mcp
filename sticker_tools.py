""" Tools for searching the Burning Man sticker archive """

import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).parent / "data" / "stickers.json"


@lru_cache(maxsize=1)
def load_stickers():
    """Read the sticker archive once and return it as a list of dictionaries."""
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"{DATA_FILE} not found. Run `uv run export_stickers.py` first."
        )
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def _text(sticker, *fields):
    """Join the given fields into one string, treating missing/null as empty."""
    return " ".join(sticker.get(field) or "" for field in fields)


def search_stickers(year=None, camp=None, keyword=None, limit=10):
    """Find stickers matching the filters given. Return a short summary of each."""
    # The year may arrive as text (e.g. "2019") from an MCP client.
    if year is not None:
        try:
            year = int(year)
        except (TypeError, ValueError):
            return "year must be a number, like 2019."

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return "limit must be a whole number."
    if limit < 1:
        return "limit must be at least 1."

    results = []
    for sticker in load_stickers():
        # Filter 1: year
        if year is not None and sticker.get("year") != year:
            continue

        # Filter 2: camp (also matches art project and art car names)
        if camp is not None:
            names = _text(sticker, "themeCampName", "artProjectName", "artCarName")
            if camp.lower() not in names.lower():
                continue

        # Filter 3: keyword
        if keyword is not None:
            text = _text(
                sticker, "title", "description", "imageAlt",
                "themeCampName", "artProjectName", "artCarName",
            )
            if keyword.lower() not in text.lower():
                continue

        results.append(sticker)

    if not results:
        return "No stickers found."

    summaries = [
        {
            "id": s.get("id"),
            "title": s.get("title"),
            "year": s.get("year"),
            "camp": s.get("themeCampName"),
            "artProject": s.get("artProjectName"),
            "artCar": s.get("artCarName"),
        }
        for s in results[:limit]
    ]
    output = json.dumps(summaries, indent=2)
    if len(results) > limit:
        output = f"Showing {limit} of {len(results)} matches:\n{output}"
    return output


def sticker_details(sticker_id):
    """Return every detail about one sticker, found by its id (slug)."""
    wanted = (sticker_id or "").strip().lower()
    for sticker in load_stickers():
        if (sticker.get("id") or "").lower() == wanted:
            return json.dumps(sticker, indent=2)
    return f"No sticker found with id '{sticker_id}'."
