from langgraph.types import Send

from matrix import story
from matrix.characters import agent_persona
from matrix.config import config
from matrix.llm import speak
from matrix.tools.agent_tools import detect_anomaly, scan_sector


def prepare_swarm(state: dict) -> dict:
    agents = list(state.get("agent_names") or config.default_agents)
    story.scene("AGENT SWARM")
    story.say(f"Deploying Agents: {', '.join(agents)}")
    story.beat("Send API fan-out — one worker per Agent")
    return {
        "agent_names": agents,
        "scene": "swarm",
        "events": [f"swarm:{','.join(agents)}"],
        "log": [f"[swarm] deploying {', '.join(agents)}"],
    }


def dispatch_agents(state: dict) -> list[Send]:
    return [
        Send(
            "agent_worker",
            {
                **state,
                "current_agent": name,
            },
        )
        for name in state["agent_names"]
    ]


def agent_worker(state: dict) -> dict:
    agent = state["current_agent"]
    sector = f"sector-{agent[0].lower()}1"
    scan = scan_sector(agent, state["city"], sector)
    anomaly = detect_anomaly(agent, state["anomaly"])

    voice = speak(
        agent_persona(agent),
        (
            f"You are Agent {agent}. Tool results: {scan}. {anomaly}. "
            "Report status in one curt sentence."
        ),
    )
    story.say(f"Agent {agent} → {state['city']}/{sector}")
    story.speak_as(f"Agent {agent}", voice)

    return {
        "sectors_scanned": [f"{state['city']}/{sector}"],
        "agent_reports": [scan, anomaly, f"{agent}: {voice}"],
        "dialogue": [f"Agent {agent}: {voice}"],
        "log": [f"[agent:{agent}] {anomaly}"],
    }


def reconcile(state: dict) -> dict:
    spoon_seen = any("spoon" in r.lower() for r in state["agent_reports"])
    story.scene("RECONCILE")
    story.say(
        f"{len(state['agent_reports'])} reports from "
        f"{len(state['sectors_scanned'])} sectors."
    )
    story.say(f"Spoon signal: {spoon_seen}")
    return {
        "spoon_exists": spoon_seen or state.get("spoon_exists", True),
        "events": [f"reconcile:spoon={spoon_seen}"],
        "log": [
            f"[reconcile] reports={len(state['agent_reports'])} "
            f"spoon={spoon_seen}"
        ],
    }


def route_reality(state: dict) -> str:
    if state["anomaly"] == "spoon" or (
        any("spoon" in r.lower() for r in state["agent_reports"])
        and state["anomaly"] != "none"
    ):
        story.beat("Conditional edge → bend_reality")
        return "bend_reality"
    story.beat("Conditional edge → enforce_reality")
    return "enforce_reality"
