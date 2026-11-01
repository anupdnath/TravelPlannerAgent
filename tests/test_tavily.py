from typing import Any

import pytest

from app import tavily
from app.config import MAX_PLACE_TEXT_CHARS, MAX_PLACES

RESULT = {"url": "https://x.test/a", "title": "Beach", "content": "Sand", "score": 0.9}


def test_build_query_uses_only_checked_fields() -> None:
    assert tavily.build_query("Goa", ["beach", "food"]) == (
        "beach food things to do in Goa"
    )
    assert tavily.build_query("Goa", []) == "things to do in Goa"


def test_parse_places_keeps_display_fields() -> None:
    assert tavily.parse_places({"results": [RESULT]}) == [
        {"title": "Beach", "url": "https://x.test/a", "summary": "Sand"}
    ]


def test_parse_places_rejects_unsafe_link_and_limits_size() -> None:
    long_result = {**RESULT, "content": "x" * 999}
    bad_result = {**RESULT, "url": "javascript:alert(1)"}
    places = tavily.parse_places({"results": [bad_result] + [long_result] * 9})
    assert len(places) == MAX_PLACES
    assert len(places[0]["summary"]) == MAX_PLACE_TEXT_CHARS


def test_clean_summary_removes_markdown_marks() -> None:
    assert tavily.clean_summary("### Zeebop ##### Relax **by** the\n\nbeach") == (
        "Zeebop Relax by the beach"
    )


async def test_search_sends_basic_depth(monkeypatch: pytest.MonkeyPatch) -> None:
    sent: dict[str, Any] = {}

    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        sent.update(arguments)
        return {"results": [RESULT]}

    monkeypatch.setattr(tavily, "call_tavily", fake_call)
    result = await tavily.search_places("Goa", ["beach"])
    assert result["available"] is True
    assert sent == {
        "query": "beach things to do in Goa",
        "search_depth": "basic",
        "max_results": MAX_PLACES,
    }


async def test_missing_key_makes_places_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("tavilyApiKey", raising=False)
    result = await tavily.search_places("Goa", [])
    assert result == {"places": [], "available": False}


async def test_failure_makes_places_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_call(arguments: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("401 with secret-value")

    monkeypatch.setattr(tavily, "call_tavily", fake_call)
    result = await tavily.search_places("Goa", [])
    assert result == {"places": [], "available": False}
