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
    "construct": Location(
        "construct",
        "The Construct",
        "White void loading dock — anything can be loaded.",
    ),
    "real_world": Location(
        "real_world",
        "Desert of the Real",
        "The ruined surface; cold air after the red pill.",
    ),
}

DEFAULT_PHYSICS = [
    "gravity",
    "solidity",
    "causality",
    "spoon_exists",
]

SCENES = (
    "jack_in",
    "architect",
    "oracle",
    "cafe",
    "swarm",
    "reality",
    "pursuit",
    "pill",
    "construct",
    "resolve",
    "operator",
)
