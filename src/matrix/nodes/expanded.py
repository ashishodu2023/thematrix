"""Expanded set pieces — Merovingian, Keymaker, Highway, Sentinels, Zion, extras."""

from __future__ import annotations

from matrix import story
from matrix.awareness import aware_node, use_state
from matrix.llm import character_act
from matrix.minds import MindStore
from matrix.objectives import scoreboard_delta
from matrix.parallel import speak_many
from matrix.physics import apply_event
from matrix.surveillance import bump_trace, tap_phone
from matrix.world import LOCATIONS


@aware_node
def merovingian_vip(state: dict) -> dict:
    loc = LOCATIONS["club_vip"]
    story.scene("ACT II — THE MEROVINGIAN")
    story.say(f"{loc.name}: {loc.description}")
    lines = speak_many(
        [
            (
                "merovingian",
                "Lecture Neo that causality, not choice, rules everything — one smug sentence.",
            ),
            (
                "persephone",
                "Quietly offer Neo a kiss of memory if he defies your husband — one intimate sentence.",
            ),
            (
                "neo",
                "React to the Merovingian's speech with stubborn defiance in one sentence.",
            ),
            (
                "trinity",
                "Warn Neo this program is dangerous — one terse sentence.",
            ),
        ],
        state=state,
    )
    story.speak_as("Merovingian", lines["merovingian"])
    story.speak_as("Persephone", lines["persephone"])
    story.speak_as("Neo", lines["neo"])
    story.speak_as("Trinity", lines["trinity"])

    # Neo defaults to defiance unless sticky already accepted causality
    sticky = dict(state.get("sticky_flags") or {})
    defy = not sticky.get("accepted_causality")
    if defy:
        sticky["defied_merovingian"] = True
        # Persephone's offer — memory kiss as sticky edge
        sticky["persephone_kiss"] = True
        board = scoreboard_delta([("neo", "defy"), ("merovingian", "accept_causality")])
        MindStore.remember("merovingian", "Neo defied causality lecture", neo_location=loc.id)
        MindStore.remember("persephone", "offered Neo a memory kiss", neo_location=loc.id)
    else:
        sticky["accepted_causality"] = True
        board = scoreboard_delta([("neo", "accept_causality")])

    tap = tap_phone(f"vip whisper @ {loc.id}")
    return {
        "location": loc.id,
        "scene": "merovingian",
        "sticky_flags": sticky,
        "dialogue": [
            f"Merovingian: {lines['merovingian']}",
            f"Persephone: {lines['persephone']}",
            f"Neo: {lines['neo']}",
            f"Trinity: {lines['trinity']}",
        ],
        "events": ["act2:merovingian", "act2:persephone"],
        "log": ["[merovingian] vip", f"[merovingian] defy={defy}"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:merovingian"],
        "phone_taps": tap.get("phone_taps") or [],
        "faction_scoreboard": board,
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc.id,
            "trinity": loc.id,
            "merovingian": loc.id,
            "persephone": loc.id,
        },
    }


@aware_node
def keymaker_doors(state: dict) -> dict:
    loc = LOCATIONS["keymaker_hall"]
    story.scene("ACT II — THE KEYMAKER")
    story.say(f"{loc.name}: {loc.description}")

    with use_state(state):
        neo_d, neo_p = character_act(
            "neo",
            ["take_key", "refuse_key"],
            (
                "The Keymaker offers the only key that matters. "
                f"meta={state.get('meta_policy')}. Choose take_key or refuse_key."
            ),
            state=state,
        )
    lines = speak_many(
        [
            (
                "keymaker",
                "Offer Neo the only key that matters — one precise helpful sentence.",
            ),
            (
                "seraph",
                "As Seraph, warn that the Keymaker is hunted — one calm protective sentence.",
            ),
        ],
        state=state,
    )
    story.speak_as("Keymaker", lines["keymaker"])
    story.speak_as("Seraph", lines["seraph"])
    story.speak_as("Neo", neo_d.speech)

    choice = neo_d.action if neo_d.action in {"take_key", "refuse_key"} else "take_key"
    sticky = dict(state.get("sticky_flags") or {})
    rules = list(state.get("physics_rules") or [])
    if choice == "take_key":
        sticky["took_key"] = True
        rules = apply_event(rules, "key_path")
        story.beat("Neo takes the key — a path through the code opens.")
        story.beat("BRANCH → highway_chase (key accepted)")
    else:
        sticky["refused_key"] = True
        story.beat("Neo refuses the key. Doors stay locked.")
        story.beat("BRANCH → city_wander (key refused)")

    board = scoreboard_delta([("neo", choice), ("keymaker", "teach")])
    MindStore.remember("keymaker", f"Neo chose {choice}", neo_location=loc.id)

    patch = {
        "location": loc.id,
        "scene": "keymaker",
        "key_choice": choice,
        "sticky_flags": sticky,
        "physics_rules": rules,
        "dialogue": [
            f"Keymaker: {lines['keymaker']}",
            f"Seraph: {lines['seraph']}",
            f"Neo: {neo_d.speech}",
        ],
        "events": [f"act2:keymaker:{choice}"],
        "log": [f"[keymaker] {choice}"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:keymaker"],
        "faction_scoreboard": board,
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc.id,
            "keymaker": loc.id,
            "seraph": loc.id,
        },
        "character_actions": list(neo_p.get("character_actions") or []),
        "agent_memory": list(neo_p.get("agent_memory") or []),
    }
    return patch


@aware_node
def highway_chase(state: dict) -> dict:
    loc = LOCATIONS["highway"]
    story.scene("ACT II — HIGHWAY CHASE")
    story.say(f"{loc.name}: {loc.description}")
    lines = speak_many(
        [
            (
                "trinity",
                "Drive the freeway chase — one urgent sentence about Agents closing in.",
            ),
            (
                "smith",
                "Pursue on the highway — one clinical hunting sentence.",
            ),
            (
                "neo",
                "React mid-chase with fear turning into focus — one short sentence.",
            ),
            (
                "niobe",
                "As Niobe on radio, bark one tactical tip for the freeway escape.",
            ),
        ],
        state=state,
    )
    for who, key in (
        ("Trinity", "trinity"),
        ("Agent Smith", "smith"),
        ("Neo", "neo"),
        ("Niobe", "niobe"),
    ):
        story.speak_as(who, lines[key])

    board = scoreboard_delta(
        [("trinity", "extract"), ("smith", "close_in"), ("neo", "dodge"), ("niobe", "cover")]
    )
    MindStore.remember("smith", "highway pursuit — Neo still free", neo_location=loc.id)
    MindStore.remember("niobe", "aided freeway extraction", neo_location=loc.id)
    trace = bump_trace(state, 8.0, "highway_chase")
    tap = tap_phone("highway police band")

    return {
        "location": loc.id,
        "scene": "highway",
        "pursuit_status": "chasing",
        "dialogue": [
            f"Trinity: {lines['trinity']}",
            f"Agent Smith: {lines['smith']}",
            f"Neo: {lines['neo']}",
            f"Niobe: {lines['niobe']}",
        ],
        "events": ["act2:highway"],
        "log": ["[highway] chase"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:highway", "agents:highway"],
        "faction_scoreboard": board,
        "trace_level": trace.get("trace_level", state.get("trace_level")),
        "phone_taps": tap.get("phone_taps") or [],
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc.id,
            "trinity": loc.id,
            "smith": loc.id,
            "niobe": loc.id,
            "brown": loc.id,
        },
    }


@aware_node
def sentinel_hunt(state: dict) -> dict:
    loc = LOCATIONS["real_world"]
    story.scene("ACT III — SENTINEL SWARM")
    story.say(f"{loc.name}: scrapers in the dark. EMP primed.")
    emp_patch: dict = {}
    try:
        from matrix.emp_game import apply_to_ship_state

        emp_patch = apply_to_ship_state(state)
    except Exception:  # noqa: BLE001
        emp_patch = {}
    destroyed = bool(state.get("ship_destroyed") or emp_patch.get("ship_destroyed"))
    heat = emp_patch.get("emp_heat", state.get("emp_heat"))
    tank_prompt = "Call EMP timing for the crew — one urgent sentence."
    if destroyed:
        tank_prompt = "Hull breached — scream one last EMP / abandon-ship sentence."
        story.beat("SHIP DESTROYED — Sentinels through the hull")
    elif heat is not None and float(heat) >= 75:
        tank_prompt = f"Hull critical heat={float(heat):.0f} — one clipped EMP order."
    lines = speak_many(
        [
            (
                "sentinel",
                "Detect the hovercraft. One mechanical hunting sentence."
                + (" Hull already open." if destroyed else ""),
            ),
            ("tank", tank_prompt),
            (
                "morpheus",
                "Steady the crew against Sentinels in one calm sentence."
                + (" The ship is dying." if destroyed else ""),
            ),
            (
                "niobe",
                "As Niobe, coordinate ship defense in one clipped sentence.",
            ),
        ],
        state=state,
    )
    story.speak_as("Sentinel", lines["sentinel"])
    story.speak_as("Tank", lines["tank"])
    story.speak_as("Morpheus", lines["morpheus"])
    story.speak_as("Niobe", lines["niobe"])
    board = scoreboard_delta(
        [("sentinel", "hunt"), ("tank", "emp"), ("morpheus", "cover"), ("niobe", "cover")]
    )
    if destroyed:
        board = scoreboard_delta(
            [("sentinel", "hunt"), ("sentinel", "hunt"), ("tank", "emp")]
        )
    sticky = dict(state.get("sticky_flags") or {})
    sticky.update(emp_patch.get("sticky_flags") or {})
    events = ["act3:sentinels"] + list(emp_patch.get("events") or [])
    if destroyed:
        events.append("act3:ship_destroyed")
    return {
        "location": loc.id,
        "scene": "sentinels",
        "sentinel_alert": True,
        "ship_destroyed": destroyed,
        "dialogue": [
            f"Sentinel: {lines['sentinel']}",
            f"Tank: {lines['tank']}",
            f"Morpheus: {lines['morpheus']}",
            f"Niobe: {lines['niobe']}",
        ],
        "events": events,
        "log": ["[sentinels] hunt"] + list(emp_patch.get("log") or []),
        "locations_visited": [loc.id],
        "active_tracks": ["machines:sentinels", "neo:ship"],
        "faction_scoreboard": board,
        "sticky_flags": sticky,
        "emp_heat": heat,
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "sentinel": loc.id,
            "tank": "nebuchadnezzar",
            "morpheus": "nebuchadnezzar",
            "niobe": "zion_dock",
        },
    }


@aware_node
def zion_dock(state: dict) -> dict:
    loc = LOCATIONS["zion_dock"]
    story.scene("ACT V — ZION DOCK")
    story.say(f"{loc.name}: {loc.description}")
    lines = speak_many(
        [
            (
                "morpheus",
                "Welcome Neo to Zion's dock with hope in one profound sentence.",
            ),
            (
                "neo",
                "First sight of Zion — one awed first-person sentence.",
            ),
            (
                "niobe",
                "As Niobe, welcome another ship home in one warm sentence.",
            ),
            (
                "tank",
                "Celebrate a successful jack-out in one warm sentence.",
            ),
        ],
        state=state,
    )
    story.speak_as("Morpheus", lines["morpheus"])
    story.speak_as("Neo", lines["neo"])
    story.speak_as("Niobe", lines["niobe"])
    story.speak_as("Tank", lines["tank"])
    board = scoreboard_delta(
        [("morpheus", "ally"), ("neo", "believe"), ("niobe", "ally"), ("tank", "call")]
    )
    return {
        "location": loc.id,
        "scene": "zion_dock",
        "dialogue": [
            f"Morpheus: {lines['morpheus']}",
            f"Neo: {lines['neo']}",
            f"Niobe: {lines['niobe']}",
            f"Tank: {lines['tank']}",
        ],
        "events": ["act5:zion_dock"],
        "log": ["[zion] dock"],
        "locations_visited": [loc.id],
        "active_tracks": ["neo:zion"],
        "faction_scoreboard": board,
        "agent_positions": {
            **(state.get("agent_positions") or {}),
            "neo": loc.id,
            "morpheus": loc.id,
            "tank": loc.id,
            "niobe": loc.id,
        },
    }
