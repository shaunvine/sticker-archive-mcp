""" Tools for searching the Burning Man sticker archive """

import json
from functools import lru_cache
from pathlib import Path

import time
from export_stickers import fetch_stickers

DATA_FILE = Path(__file__).parent / "data" / "stickers.json"

CACHE_SECONDS = 10 * 60 # remember live data for 10 minutes
_cache = {"stickers": None, "fetched_at": 0.0}

def load_stickers():
    """Return all stickers: live from Contentful, remembered for 10 minutes.
    Falls back to data/stickers.json if Contentful can't be reached."""
    now = time.time()

    # 1. Recently fetched? Use the remembered copy.
    if _cache["stickers"] is not None and now - _cache["fetched_at"] < CACHE_SECONDS:
        return _cache["stickers"]

    # 2. Otherwise, try Contentful.
    try:
        stickers = fetch_stickers()
    except Exception:
        # 3. Contentful failed: use the last copy, or the file.
        if _cache["stickers"] is not None:
            return _cache["stickers"]
        return _load_from_file()

    # 4. It worked: remember the stickers and the time, then return them.
    _cache["stickers"] = stickers
    _cache["fetched_at"] = now
    return stickers


@lru_cache(maxsize=1)
def _load_from_file():
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


def _has_file_name(text):
    """Return True if any word in the text ends with an image file extension."""
    extensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")

    # split() breaks the text into words at spaces.
    for word in text.lower().split():
        # Remove punctuation from the end of the word, e.g. "photo.png," -> "photo.png"
        word = word.rstrip(",.;:!?\"'()")
        for extension in extensions:
            if word.endswith(extension):
                return True

    return False


def alt_text_audit(limit=20):
    """Check every sticker's imageAlt and list the ones that look weak."""
    # Check limit the same way search_stickers does.
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        return "limit must be a whole number."
    if limit < 1:
        return "limit must be at least 1."

    stickers = load_stickers()
    flagged = []

    for sticker in stickers:
        # "or ''" turns a missing value (None) into an empty string.
        alt = (sticker.get("imageAlt") or "").strip()
        title = (sticker.get("title") or "").strip()
        alt_lower = alt.lower()
        title_lower = title.lower()

        reasons = []

        # Rule 1: missing or blank
        if alt == "":
            reasons.append("Alt text is missing or blank.")

        # Rule 2: too short (blank is already covered by rule 1)
        if alt != "" and len(alt) < 20:
            reasons.append("Alt text is under 20 characters.")

        # Rule 3: same as the title, ignoring capitals and outer spaces
        if alt != "" and alt_lower == title_lower:
            reasons.append("Alt text is the same as the title.")

        # Rule 4: starts with a phrase screen readers already announce
        if alt_lower.startswith(("image of", "picture of", "photo of")):
            reasons.append(
                "Alt text starts with 'image of', 'picture of' or 'photo of'."
            )

        # Rule 5: too long
        if len(alt) > 250:
            reasons.append("Alt text is over 250 characters.")

        # Rule 6: looks like it contains a file name
        if _has_file_name(alt):
            reasons.append("Alt text contains a file name.")

        # Keep the sticker only if it has at least one reason.
        if len(reasons) > 0:
            flagged.append(
                {
                    "id": sticker.get("id"),
                    "title": sticker.get("title"),
                    "year": sticker.get("year"),
                    "imageAlt": sticker.get("imageAlt"),
                    "reasons": reasons,
                }
            )

    total = len(stickers)
    if len(flagged) == 0:
        return f"All {total} stickers passed the alt-text audit."

    output = f"{len(flagged)} of {total} stickers need attention"
    if len(flagged) > limit:
        output += f"\nShowing {limit} of {len(flagged)}"
    output += "\n" + json.dumps(flagged[:limit], indent=2)
    return output


def sticker_details(sticker_id):
    """Return every detail about one sticker, found by its id (slug)."""
    wanted = (sticker_id or "").strip().lower()
    for sticker in load_stickers():
        if (sticker.get("id") or "").lower() == wanted:
            return json.dumps(sticker, indent=2)
    return f"No sticker found with id '{sticker_id}'."
