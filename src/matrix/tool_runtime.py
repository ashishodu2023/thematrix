"""Bindable in-sim tools — Agents/Operator can invoke via TOOL: lines."""

from __future__ import annotations

import re
from typing import Any, Callable

from matrix.tools import agent_tools, operator_tools
from matrix.surveillance import bump_trace, hardline_available, tap_phone, use_hardline

ToolFn = Callable[[dict, str], dict[str, Any]]

_TOOL_LINE = re.compile(
    r"(?im)^\s*TOOL\s*:\s*([a-z_]+)\s*(?:\((.*?)\))?\s*$"
)


def _arg(raw: str | None) -> str:
    return (raw or "").strip().strip("\"'")


def tool_scan(state: dict, arg: str) -> dict[str, Any]:
    agent = str(state.get("current_agent") or "smith")
    sector = arg or str(state.get("location") or "unknown")
    city = str(state.get("city") or "Mega City")
    report = agent_tools.scan_sector(agent, city, sector)
    return {
        "agent_reports": [report],
        "sectors_scanned": [sector],
        "log": [f"[tool] scan {sector}"],
        "events": [f"tool:scan:{sector}"],
        "tool_result": report,
    }


def tool_detect(state: dict, arg: str) -> dict[str, Any]:
    agent = str(state.get("current_agent") or "smith")
    anomaly = arg or str(state.get("anomaly") or "none")
    report = agent_tools.detect_anomaly(agent, anomaly)
    return {
        "agent_reports": [report],
        "log": [f"[tool] detect {anomaly}"],
        "events": [f"tool:detect:{anomaly}"],
        "tool_result": report,
    }


def tool_tap(state: dict, arg: str) -> dict[str, Any]:
    line = arg or f"line@{state.get('location')}"
    patch = tap_phone(line)
    extra = bump_trace(state, 4.0, f"tool_tap:{line[:20]}")
    patch["trace_level"] = extra.get("trace_level")
    patch["events"] = list(patch.get("events") or []) + list(extra.get("events") or [])
    patch["tool_result"] = f"tapped {line}"
    return patch


def tool_hardline(state: dict, arg: str) -> dict[str, Any]:
    if not hardline_available(state):
        return {
            "ok": False,
            "tool_result": "hardline cooling",
            "log": ["[tool] hardline blocked"],
            "events": ["tool:hardline_blocked"],
        }
    patch = use_hardline(state)
    patch["tool_result"] = "hardline used"
    return patch


def tool_emp(state: dict, arg: str) -> dict[str, Any]:
    patch = operator_tools.emp_pulse(state)
    patch["tool_result"] = "EMP discharged"
    return patch


def tool_cctv(state: dict, arg: str) -> dict[str, Any]:
    sector = arg or str(state.get("location") or "jack_point")
    patch = operator_tools.watch_cctv(state, sector)
    patch["tool_result"] = f"CCTV {sector}"
    return patch


def tool_load_skill(state: dict, arg: str) -> dict[str, Any]:
    patch = operator_tools.load_skill(state, arg or "kung_fu")
    patch["tool_result"] = f"loaded {arg or 'kung_fu'}"
    return patch


AGENT_TOOLS: dict[str, ToolFn] = {
    "scan": tool_scan,
    "detect": tool_detect,
    "tap": tool_tap,
}

OPERATOR_TOOLS: dict[str, ToolFn] = {
    "hardline": tool_hardline,
    "emp": tool_emp,
    "cctv": tool_cctv,
    "load_skill": tool_load_skill,
    "tap": tool_tap,
}

ALL_TOOLS: dict[str, ToolFn] = {**AGENT_TOOLS, **OPERATOR_TOOLS}


def tool_catalog(kind: str = "agent") -> str:
    names = list(AGENT_TOOLS if kind == "agent" else OPERATOR_TOOLS)
    return ", ".join(names)


def parse_tool_calls(raw: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in _TOOL_LINE.finditer(raw or ""):
        out.append((m.group(1).lower(), _arg(m.group(2))))
    return out


def run_tools(
    state: dict,
    raw: str,
    *,
    allowed: dict[str, ToolFn] | None = None,
) -> dict[str, Any]:
    """Execute TOOL: lines found in an LLM reply; merge patches."""
    catalog = allowed or ALL_TOOLS
    merged: dict[str, Any] = {"tool_results": []}
    for name, arg in parse_tool_calls(raw):
        fn = catalog.get(name)
        if not fn:
            merged["tool_results"].append(f"{name}: unknown")
            continue
        try:
            patch = fn(state, arg)
        except Exception as exc:  # noqa: BLE001
            merged["tool_results"].append(f"{name}: error {exc}")
            continue
        for k, v in patch.items():
            if k in {"events", "log", "agent_reports", "sectors_scanned", "phone_taps", "tool_results"}:
                merged[k] = list(merged.get(k) or []) + list(v if isinstance(v, list) else [v])
            elif k == "tool_result":
                merged["tool_results"].append(f"{name}: {v}")
            else:
                merged[k] = v
        # apply into working state for chained tools
        state = {**state, **{kk: vv for kk, vv in patch.items() if kk != "tool_result"}}
    return merged
