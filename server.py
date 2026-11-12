"""MCP server for the Burning Man Sticker Archive"""

from fastmcp import FastMCP

import sticker_tools

mcp = FastMCP("sticker-archive")

@mcp.tool()
def search_stickers(
    year: int | None = None,
    camp: str | None = None,
    keyword: str | None = None,
    limit: int = 10,
) -> str:
    """Search the Burning Man sticker archive (396 stickers, 1999 to 2026).

    Use this when the user wants to find or list stickers. Filters can be combined:
    - year: the year of the sticker, e.g. 2019
    - camp: part of a theme camp, art project or art car name, e.g. "balls"
    - keyword: a word to look for in the title, description or alt text
    Returns a short summary of each match, with its id. If there are more
    matches than the limit, the result starts with "Showing X of Y matches".
    """
    return sticker_tools.search_stickers(year=year, camp=camp, keyword=keyword, limit=limit)

@mcp.tool()
def sticker_details(sticker_id: str) -> str:
    """Get every detail about one sticker: title, year, description, image, alt text, themes, camp and credits.

    Use the id from search_stickers, e.g. "2011-model".
    """
    return sticker_tools.sticker_details(sticker_id)


@mcp.tool()
def alt_text_audit(limit: int = 20) -> str:
    """Audit the alt text of every sticker image on burningmanstickers.org
    for accessibility problems.

    Checks for alt text that is missing, under 20 characters, the same as the
    title, starts with "image of", is over 250 characters, or contains a file name.

    Use this when the user asks:
    - Do the images have meaningful alt text for screen readers?
    - Do the images have alt text?
    - How accessible are the sticker images?
    """
    return sticker_tools.alt_text_audit(limit=limit)
    
if __name__ == "__main__":
        mcp.run(transport="stdio")