from datetime import date

from app.events import QUEUE_SIZE, EventHub, safe_changes


def test_safe_changes_drops_query_and_counts_results() -> None:
    changes = safe_changes(
        {
            "query": "private text",
            "destination": "Goa",
            "check_in": date(2026, 12, 10),
            "stay_candidates": [{"name": "Stay"}],
            "places": [],
            "extracted": True,
        }
    )
    assert changes == {
        "destination": "Goa",
        "check_in": "2026-12-10",
        "stay_candidates_count": 1,
        "places_count": 0,
    }


def test_safe_changes_accepts_no_update() -> None:
    assert safe_changes(None) == {}


async def test_hub_sends_to_each_subscriber_until_unsubscribed() -> None:
    hub = EventHub()
    first = hub.subscribe()
    second = hub.subscribe()
    hub.publish({"kind": "a"})
    hub.unsubscribe(second)
    hub.publish({"kind": "b"})
    assert first.qsize() == 2
    assert second.qsize() == 1


async def test_slow_page_loses_oldest_event_and_never_blocks() -> None:
    hub = EventHub()
    queue = hub.subscribe()
    for number in range(QUEUE_SIZE + 3):
        hub.publish({"number": number})
    assert queue.qsize() == QUEUE_SIZE
    assert queue.get_nowait() == {"number": 3}
