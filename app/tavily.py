"""FastMCP client for the Tavily MCP server. Places are optional for a trip."""

import json
import re
from typing import Any

from loguru import logger

from app.config import MAX_PLACE_TEXT_CHARS, MAX_PLACES
from app.mcp_client import MCP_FAILURES, is_https_url, open_client


def build_query(destination: str, interests: list[str]) -> str:
    """Build the search text from checked fields, never from the customer message."""
    words = " ".join(interests)
    return f"{words} things to do in {destination}".strip()


def clean_summary(text: str) -> str:
    """Remove markdown marks and extra spaces from web text, then limit the length."""
    plain = re.sub(r"[#*_`|]+", " ", text)
    return " ".join(plain.split())[:MAX_PLACE_TEXT_CHARS]


def parse_places(payload: dict[str, Any]) -> list[dict[str, str]]:
    places = []
    for raw in payload.get("results") or []:
        if not is_https_url(raw.get("url")):
            logger.warning("ACTION: parse_places | rejected a result with no safe link")
            continue
        places.append(
            {
                "title": raw.get("title") or raw["url"],
                "url": raw["url"],
                "summary": clean_summary(raw.get("content") or ""),
            }
        )
    return places[:MAX_PLACES]


async def call_tavily(arguments: dict[str, Any]) -> dict[str, Any]:
    """Call tavily_search over MCP. Return the payload of the tool result."""
    async with open_client("tavily") as client:
        result = await client.call_tool(
            "tavily_search", arguments, raise_on_error=False
        )
    if result.is_error:
        raise RuntimeError("tavily_search returned an error")
    return result.structured_content or json.loads(result.content[0].text)


async def search_places(destination: str, interests: list[str]) -> dict[str, Any]:
    arguments = {
        "query": build_query(destination, interests),
        "search_depth": "basic",
        "max_results": MAX_PLACES,
    }
    logger.info(f"MCP tavily_search | arguments={arguments}")
    try:
        places = parse_places(await call_tavily(arguments))
    except MCP_FAILURES as e:
        # Log the type only, because a connection error can include request details.
        logger.warning(f"FAILED: tavily_search | reason={type(e).__name__}")
        return {"places": [], "available": False}
    logger.success(f"MCP tavily_search | places={len(places)}")
    return {"places": places, "available": True}
