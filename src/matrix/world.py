"""World map, physics, and scene catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Location:
    id: str
    name: str
    description: str


LOCATIONS: dict[str, Location] = {
    "jack_point": Location(
        "jack_point",
        "Jack-in Point",
        "Hardline phone booth on the edge of Mega City.",
    ),
    "apartment": Location(
        "apartment",
        "Neo's Apartment",
        "Stacks of monitors; the word Wake Up flashes green.",
    ),
    "club": Location(
        "club",
        "The Club",
        "Bass and bodies; Trinity finds you in the crowd.",
    ),
    "oracle_apartment": Location(
        "oracle_apartment",
        "The Oracle's Apartment",
        "Warm kitchen smells of cookies; the future sits at the table.",
    ),
    "cafe": Location(
        "cafe",
        "The Spoon Cafe",
        "A quiet cafe where a child bends silverware with belief.",
    ),
    "hotel_lobby": Location(
        "hotel_lobby",
        "Government Lobby",
        "Marble floors, pillars, and a security desk that will not last.",
    ),
    "subway": Location(
        "subway",
        "Mega City Subway",
        "Crowded tunnels — Agents can overwrite any face here.",
    ),
    "rooftop": Location(
        "rooftop",
        "Rooftop Chase",
        "Rain-slick concrete; gravity is optional if you believe.",
    ),
    "highway": Location(
        "highway",
        "Mega City Highway",
        "Trucks as cover; Agents rewrite drivers mid-pursuit.",
    ),
    "construct": Location(
        "construct",
        "The Construct",
        "White void loading dock — anything can be loaded.",
    ),
    "nebuchadnezzar": Location(
        "nebuchadnezzar",
        "Nebuchadnezzar",
        "Hovercraft of rusty steel; Zion's thin line of hope.",
    ),
    "real_world": Location(
        "real_world",
        "Desert of the Real",
        "The ruined surface; cold air after the red pill.",
    ),
    "club_vip": Location(
        "club_vip",
        "Merovingian VIP",
        "Velvet booths; causality served with wine and contempt.",
    ),
    "keymaker_hall": Location(
        "keymaker_hall",
        "Keymaker's Hall",
        "Endless keys on hooks — every door is a decision.",
    ),
    "zion_dock": Location(
        "zion_dock",
        "Zion Dock",
        "Docking clamps and cheering rebels under the earth.",
    ),
}

DEFAULT_PHYSICS = [
    "gravity",
    "solidity",
    "causality",
    "spoon_exists",
]
