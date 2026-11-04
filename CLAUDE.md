# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Task

Write export_stickers.py. Read the three values from .env with python-dotenv. Fetch all bmSticker entries from the Contentful Delivery API (cdn.contentful.com) with requests, 1000 at a time until there are none left. Save a simplified list to data/stickers.json, using slug as each sticker's id. Keep: title, slug, year, description, imageUrl, imageAlt, officialTheme, bmTheme, shape, themeCampName, campLink, artProjectName, artProjectLink, artCarName, artCarLink, officialSticker, featuredSticker, createdBy, creatorInfo, contributor.

## Safety

- Never edit, commit or push in the burningmanstickers.org repo.
- Only read from Contentful (delivery API). Never create, edit or delete content.
- Never show, print or store access token values in chat or in files committed to GitHub.
- Never read or display .env. To check keys exist, print key names only, never values.
  Explain each part before writing it.

## Commands

Python >=3.14, dependencies managed with `uv` (`pyproject.toml` / `uv.lock`). There are no tests or linter configured.

- `uv sync` — install dependencies into `.venv`
- `uv run export_stickers.py` — fetch all bmSticker entries and write `data/stickers.json`

## Architecture

`export_stickers.py` is a single-script, read-only export from Contentful. The pipeline is `load_config` → `fetch_all` → `simplify` (per entry) → JSON dump.

- `.env` must define `CONTENTFUL_SPACE_ID`, `CONTENTFUL_ENVIRONMENT_ID` and `CONTENTFUL_DELIVERY_TOKEN`. The token is sent only in the `Authorization` header, never in the URL, so it can't leak through URLs or error text. Error output prints the HTTP status only.
- Pagination uses `limit=1000` with `skip`, ordered by `sys.id` so pages are stable, and stops when a page returns no items. Linked assets arrive in each response's `includes.Asset` and are collected by id.
- `simplify` details that aren't obvious from the field list:
  - `id` is the `slug`, falling back to `sys.id` when the slug is missing or blank (the script reports how many fell back).
  - `description` is Rich Text, flattened to plain text by `rich_text_to_text`.
  - `imageUrl` is resolved from the linked asset (`fields.image` → `includes.Asset`) and prefixed with `https:`.
  - Blank or whitespace-only strings become `null`.
- `KEPT_FIELDS` holds the straight copy-through fields. `description` and `imageUrl` are derived separately, so add new plain fields to `KEPT_FIELDS`.
- `data/stickers.json` is the output and is meant to feed the MCP server this repo is named for (`mcp` is already a dependency). `.env` and `.venv` are gitignored. `data/` is not.
