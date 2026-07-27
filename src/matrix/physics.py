"""Physics / code layer — belief and rules change chase and showdown odds."""

from __future__ import annotations


def normalize_rules(rules: list[str] | None) -> list[str]:
    out: list[str] = []
    for r in rules or []:
        key = str(r).strip().lower()
        if key and key not in out:
            out.append(key)
    return out


def apply_event(rules: list[str], event: str) -> list[str]:
    """Mutate physics from a story event."""
    r = normalize_rules(rules)
    ev = event.strip().lower()
    if ev == "bend_spoon":
        r = [x for x in r if x != "spoon_exists"]
        if "belief_over_rules" not in r:
            r.append("belief_over_rules")
    elif ev == "code_sight":
        if "code_sight" not in r:
            r.append("code_sight")
    elif ev == "glitch":
        if "deja_vu" not in r:
            r.append("deja_vu")
    elif ev == "key_path":
        if "key_path" not in r:
            r.append("key_path")
    elif ev == "enforce":
        for needed in ("gravity", "solidity", "causality", "spoon_exists"):
            if needed not in r:
                r.append(needed)
        r = [
            x
            for x in r
            if x not in {"belief_over_rules", "code_sight", "deja_vu", "key_path"}
        ]
    return r


def chase_modifiers(state: dict) -> dict[str, float]:
    """
    Return additive modifiers for escape_chance / catch_chance.
    Positive escape helps Neo; positive catch helps Agents.
    """
    rules = set(normalize_rules(state.get("physics_rules")))
    escape = 0.0
    catch = 0.0
    if "belief_over_rules" in rules or state.get("reality_rewritten"):
        escape += 0.12
        catch -= 0.08
    if "code_sight" in rules:
        escape += 0.10
        catch -= 0.05
    if "deja_vu" in rules:
        escape += 0.06
        catch += 0.03
    if "key_path" in rules:
        escape += 0.08
    if "spoon_exists" in rules and not state.get("reality_rewritten"):
        catch += 0.05
    if state.get("bug_implanted"):
        catch += 0.15
        escape -= 0.10
    sticky = state.get("sticky_flags") or {}
    if sticky.get("cypher_deal"):
        catch += 0.10
    if sticky.get("walked_from_trinity"):
        escape -= 0.05
    if sticky.get("trusted_trinity"):
        escape += 0.05
    if sticky.get("took_key"):
        escape += 0.07
    if sticky.get("defied_merovingian"):
        catch += 0.04
    policy = str(state.get("meta_policy") or "").lower()
    if policy == "control":
        catch += 0.10
        escape -= 0.05
    elif policy == "choice":
        escape += 0.10
        catch -= 0.05
    elif policy == "contested":
        escape += 0.03
        catch += 0.03
    elif policy == "purge":
        catch += 0.14
    try:
        from matrix.minds import MindStore

        smith = MindStore.load("smith")
        if smith.grudge:
            catch += 0.06
        if smith.last_known_neo_location and smith.last_known_neo_location == state.get(
            "location"
        ):
            catch += 0.05
        cypher = MindStore.load("cypher")
        if sticky.get("cypher_deal") or "steak" in (cypher.grudge or "").lower():
            catch += 0.04
    except Exception:  # noqa: BLE001
        pass
    trace = float(state.get("trace_level") or 0)
    catch += min(0.25, trace / 100.0)
    escape -= min(0.15, trace / 150.0)
    heat = state.get("sector_heat") or {}
    loc = str(state.get("location") or "")
    if loc and heat:
        catch += min(0.12, float(heat.get(loc, 0)) / 40.0)
    taps = state.get("phone_taps") or []
    if taps:
        catch += min(0.10, 0.03 * len(taps))
    return {"escape": escape, "catch": catch}


def showdown_win_threshold(state: dict) -> int:
    """Training score needed to 'win' showdown (default 6)."""
    base = 6
    rules = set(normalize_rules(state.get("physics_rules")))
    if "code_sight" in rules:
        base -= 1
    if "key_path" in rules:
        base -= 1
    if state.get("bug_implanted"):
        base += 1
    policy = str(state.get("meta_policy") or "").lower()
    if policy == "control":
        base += 1
    elif policy == "choice":
        base -= 1
    return max(4, base)
