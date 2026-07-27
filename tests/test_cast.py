"""Cast map placement tests."""

from matrix.cast import ensure_cast, seed_positions
from matrix.tick import world_tick


def test_seed_has_full_cast():
    pos = seed_positions()
    for name in (
        "neo",
        "trinity",
        "morpheus",
        "tank",
        "cypher",
        "oracle",
        "spoon_boy",
        "architect",
        "smith",
        "jones",
        "brown",
        "merovingian",
        "keymaker",
        "sentinel",
    ):
        assert name in pos


def test_ensure_cast_pins_neo_and_copilot():
    pos = ensure_cast(
        {
            "location": "cafe",
            "co_human_id": "trinity",
            "scene": "oracle_visit",
            "agent_positions": {"smith": "subway"},
        }
    )
    assert pos["neo"] == "cafe"
    assert pos["trinity"] == "cafe"
    assert pos["smith"] == "subway"
    assert "oracle" in pos


def test_world_tick_keeps_cast():
    state = {
        "location": "apartment",
        "agent_names": ["Smith", "Jones", "Brown"],
        "agent_positions": seed_positions(),
        "world_tick": 0,
        "threat_level": 4,
        "trace_level": 0.0,
        "hardline_cooldown": 0,
        "sector_heat": {},
        "phone_taps": [],
        "co_human_id": "trinity",
    }
    out = world_tick(state)
    assert len(out["agent_positions"]) >= 11
    assert out["agent_positions"]["neo"] == "apartment"
    assert out["agent_positions"]["trinity"] == "apartment"
