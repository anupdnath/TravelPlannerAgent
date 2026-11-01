"""Build Prefab views. The tools return them as JSON, and app.js draws them."""

from typing import Any

from prefab_ui import PrefabApp
from prefab_ui.actions.mcp import CallTool
from prefab_ui.components import (
    H3,
    Button,
    Column,
    DatePicker,
    Input,
    Label,
    Link,
    Radio,
    RadioGroup,
    Text,
)

from app.airbnb import SOURCE_SAMPLE

BUDGET_OPTIONS = [
    ("10000", "₹10,000"),
    ("25000", "₹25,000"),
    ("50000", "₹50,000"),
    ("100000", "₹1,00,000"),
]


def _radio_field(name: str, title: str, options: list[tuple[str, str]]) -> None:
    Label(title, id=f"{name}-label")
    with RadioGroup(name=name, aria_labelledby=f"{name}-label"):
        for value, label in options:
            Radio(option=value, label=label, id=f"{name}-{value}")


def _draw_field(name: str) -> None:
    if name == "destination":
        Label("Destination", id="destination-label")
        Input(name="destination", placeholder="Goa", id="destination")
    elif name == "check_in":
        Label("Check-in date", id="check_in-label")
        DatePicker(name="check_in", id="check_in")
    elif name == "check_out":
        Label("Check-out date", id="check_out-label")
        DatePicker(name="check_out", id="check_out")
    elif name == "adults":
        Label("Number of adults", id="adults-label")
        Input(name="adults", input_type="number", placeholder="2", id="adults")
    elif name == "budget_total_inr":
        _radio_field("budget_total_inr", "Budget for the whole trip", BUDGET_OPTIONS)


def build_form(
    thread_id: str, missing_fields: list[str], error: str | None
) -> PrefabApp:
    """Build a form with one control for each missing field."""
    arguments = {"thread_id": thread_id}
    arguments.update({name: f"{{{{ {name} }}}}" for name in missing_fields})
    state = {name: "" for name in missing_fields}
    with PrefabApp(state=state) as app, Column(gap=3):
        H3("We need a few more details")
        if error:
            Text(error, css_class="error")
        for name in missing_fields:
            _draw_field(name)
        Button(
            "Search stays",
            on_click=CallTool("submit_trip_details", arguments=arguments),
        )
    return app


def _draw_places(
    destination: str, places: list[dict[str, str]], available: bool
) -> None:
    H3(f"Things to do in {destination}")
    if not available:
        Text("Places are not available right now.")
    elif not places:
        Text("The web search found no places.")
    for place in places:
        with Column(gap=1, css_class="listing"):
            Link(place["title"], href=place["url"])
            Text(place["summary"])


def build_results(
    destination: str,
    listings: list[dict[str, Any]],
    source: str,
    places: list[dict[str, str]],
    places_available: bool,
) -> PrefabApp:
    with PrefabApp() as app, Column(gap=3):
        if source == SOURCE_SAMPLE:
            Text(
                "SAMPLE DATA. The live Airbnb search failed. These are recorded "
                "Goa listings, not results for your search.",
                css_class="error",
            )
            H3("Sample stays")
        else:
            H3(f"Stays in {destination}")
        if not listings:
            Text("Airbnb returned no stays for these details.")
        for listing in listings:
            with Column(gap=1, css_class="listing"):
                Link(listing["name"], href=listing["url"])
                Text(listing["details"])
                Text(listing["price"])
                Text(listing["rating"])
        _draw_places(destination, places, places_available)
    return app


def build_error(code: str, detail: str) -> PrefabApp:
    """Show one error. The state holds the structured error response."""
    state = {"status": "error", "code": code, "detail": detail}
    with PrefabApp(state=state) as app:
        Text(detail, css_class="error")
    return app
