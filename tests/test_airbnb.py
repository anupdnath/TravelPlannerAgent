from datetime import date
from typing import Any

import pytest

from app import airbnb

RAW: dict[str, Any] = {
    "id": "7",
    "url": "https://www.airbnb.co.in/rooms/7",
    "demandStayListing": {
        "description": {
            "name": {"localizedStringWithTranslationPreference": "Sea Flat"}
        }
    },
    "structuredContent": {"primaryLine": "1 bedroom"},
    "avgRatingA11yLabel": "4.9 out of 5",
    "structuredDisplayPrice": {
        "primaryLine": {"accessibilityLabel": "₹12,000 for 3 nights"}
    },
}
SEARCH: dict[str, Any] = {
    "destination": "Goa",
    "check_in": date(2026, 12, 10),
    "check_out": date(2026, 12, 13),
    "adults": 2,
    "max_price_per_night": 6000,
}


def test_parse_listing_keeps_display_fields() -> None:
    listing = airbnb.parse_listing(RAW)
    assert listing is not None
    assert listing["name"] == "Sea Flat"
    assert listing["price"] == "₹12,000 for 3 nights"


@pytest.mark.parametrize("url", ["javascript:alert(1)", "https://", None, 7])
def test_parse_listing_rejects_unsafe_link(url: Any) -> None:
    assert airbnb.parse_listing({**RAW, "url": url}) is None


def test_parse_search_limits_listings() -> None:
    assert len(airbnb.parse_search({"searchResults": [RAW] * 9})) == airbnb.MAX_LISTINGS


async def test_search_sends_mcp_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, Any] = {}

    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        sent.update(arguments)
        return {"searchResults": [RAW]}

    monkeypatch.setattr(airbnb, "call_airbnb", fake_call)
    result = await airbnb.search_stays(**SEARCH)
    assert result["source"] == airbnb.SOURCE_LIVE
    assert sent["checkin"] == "2026-12-10"
    assert sent["maxPrice"] == 6000


async def test_empty_live_search_is_not_sample_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        return {"searchResults": []}

    monkeypatch.setattr(airbnb, "call_airbnb", fake_call)
    result = await airbnb.search_stays(**SEARCH)
    assert result == {"listings": [], "source": airbnb.SOURCE_LIVE}


async def test_tool_error_uses_sample_data(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        return {"error": "Failed to parse"}

    monkeypatch.setattr(airbnb, "call_airbnb", fake_call)
    result = await airbnb.search_stays(**SEARCH)
    assert result["source"] == airbnb.SOURCE_SAMPLE
    assert len(result["listings"]) == 5


async def test_server_crash_uses_sample_data(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        raise OSError("node not found")

    monkeypatch.setattr(airbnb, "call_airbnb", fake_call)
    result = await airbnb.search_stays(**SEARCH)
    assert result["source"] == airbnb.SOURCE_SAMPLE


async def test_changed_page_shape_uses_sample_data(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        return {"searchResults": [{**RAW, "demandStayListing": "changed"}]}

    monkeypatch.setattr(airbnb, "call_airbnb", fake_call)
    result = await airbnb.search_stays(**SEARCH)
    assert result["source"] == airbnb.SOURCE_SAMPLE
