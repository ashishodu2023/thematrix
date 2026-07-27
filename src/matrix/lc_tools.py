"""LangChain tool binding helpers — bind_tools when Ollama supports it."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from matrix.tool_runtime import AGENT_TOOLS, OPERATOR_TOOLS, run_tools


class _ScanArgs(BaseModel):
    sector: str = Field(default="", description="Sector to scan")


class _DetectArgs(BaseModel):
    anomaly: str = Field(default="", description="Anomaly label")


class _TapArgs(BaseModel):
    line: str = Field(default="", description="Phone line id")


class _HardlineArgs(BaseModel):
    note: str = Field(default="", description="Optional note")


class _EmpArgs(BaseModel):
    note: str = Field(default="", description="Optional note")


class _CctvArgs(BaseModel):
    sector: str = Field(default="", description="Sector to watch")


class _SkillArgs(BaseModel):
    skill: str = Field(default="kung_fu", description="Construct skill")


def _wrap(name: str, catalog: dict) -> StructuredTool:
    fn = catalog[name]

    def _call(**kwargs: Any) -> str:
        # Placeholder — real execution happens via run_tools on tool_calls / TOOL lines
        arg = next(iter(kwargs.values()), "") if kwargs else ""
        return f"{name}({arg})"

    schema = {
        "scan": _ScanArgs,
        "detect": _DetectArgs,
        "tap": _TapArgs,
        "hardline": _HardlineArgs,
        "emp": _EmpArgs,
        "cctv": _CctvArgs,
        "load_skill": _SkillArgs,
    }.get(name, _ScanArgs)

    return StructuredTool.from_function(
        func=_call,
        name=name,
        description=f"Matrix sim tool: {name}",
        args_schema=schema,
    )


def langchain_tools(kind: str = "agent") -> list[StructuredTool]:
    catalog = OPERATOR_TOOLS if kind == "operator" else AGENT_TOOLS
    return [_wrap(n, catalog) for n in catalog]


def tool_calls_to_raw(tool_calls: list[Any]) -> str:
    """Serialize LC tool_calls into TOOL: lines for run_tools."""
    lines: list[str] = []
    for tc in tool_calls or []:
        if isinstance(tc, dict):
            name = tc.get("name") or ""
            args = tc.get("args") or {}
        else:
            name = getattr(tc, "name", "") or ""
            args = getattr(tc, "args", {}) or {}
        if not name:
            continue
        arg = ""
        if isinstance(args, dict) and args:
            arg = str(next(iter(args.values())))
        lines.append(f"TOOL: {name}({arg})" if arg else f"TOOL: {name}")
    return "\n".join(lines)


def try_bound_invoke(
    llm: Any,
    messages: list,
    *,
    kind: str,
    state: dict,
) -> tuple[str, dict[str, Any]] | None:
    """
    Attempt bind_tools + invoke. Returns (text, patches) or None to fall back.
    """
    try:
        tools = langchain_tools(kind)
        bound = llm.bind_tools(tools)
        resp = bound.invoke(messages)
    except Exception:  # noqa: BLE001
        return None

    content = getattr(resp, "content", "") or ""
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and "text" in block:
                parts.append(str(block["text"]))
            else:
                parts.append(str(block))
        text = " ".join(parts)
    else:
        text = str(content)

    tool_calls = getattr(resp, "tool_calls", None) or []
    raw_extra = tool_calls_to_raw(tool_calls)
    combined = (text + ("\n" + raw_extra if raw_extra else "")).strip()
    allowed = OPERATOR_TOOLS if kind == "operator" else AGENT_TOOLS
    patches = run_tools({**state, "current_agent": state.get("current_agent", "smith")}, combined, allowed=allowed)
    return combined, patches
