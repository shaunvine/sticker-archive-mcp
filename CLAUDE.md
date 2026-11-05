# CLAUDE.md

Guidance for Claude Code when working in this repository.

## How to work with me

I'm learning MCP and Python (junior level). Teach as you go.

- Explain what you're about to do, and why, before doing it.
- Use plain, modern UK English. Avoid jargon or explain it.
- When I'm writing core logic (tools and server code), guide me step by step and review what I type. Don't write it for me unless I ask.
- Setup, config and boilerplate: you may write these, but explain each line.
- When I ask for a review, don't change files. Explain any problems instead.
- Make only the change I ask for, one small change at a time. If you think something else should change, suggest it and wait for my OK.
- Use the standalone fastmcp package, version 3 (`from fastmcp import FastMCP`), with mcp below 2.
- Keep tools in sticker_tools.py and the server in server.py.
- At the end of each stage, remind me to update README.md and commit before moving on.

## Safety

- Never edit, commit or push in the burningmanstickers.org repo.
- Only read from Contentful (delivery API). Never create, edit or delete content.
- Never show, print or store access token values in chat or in files committed to GitHub.
- Never read or display .env. To check keys exist, print key names only, never values.

## Commands

Python >=3.14, dependencies managed with `uv` (`pyproject.toml` / `uv.lock`). No tests or linter configured yet.

- `uv sync`: install dependencies into `.venv`
- `uv run export_stickers.py`: fetch all bmSticker entries from Contentful and write `data/stickers.json`
- `uv run server.py`: start the MCP server (stdio; it waits silently for a host)
- `npx @modelcontextprotocol/inspector uv run server.py`: test the tools in the MCP Inspector

## Architecture

- `export_stickers.py`: read-only export from Contentful. `load_config` → `fetch_all` → `simplify` (per entry) → JSON dump. The token is sent only in the `Authorization` header. `id` is the slug (falling back to `sys.id`), `description` is Rich Text flattened to plain text, `imageUrl` is resolved from the linked asset, and blank strings become `null`.
- `sticker_tools.py`: the real logic, as plain functions (`load_stickers`, `search_stickers`, `sticker_details`). `load_stickers` is cached with `@lru_cache`, so restart the server after re-exporting data.
- `server.py`: thin FastMCP wrappers. Docstrings and type hints become what Claude sees. Pass arguments to `sticker_tools` **by name**, not by position. No `print()` in server code (stdio uses standard output for messages).
- `data/stickers.json` is committed (public data). `.env`, `.venv`, `.DS_Store` and `.vscode/` are gitignored.
