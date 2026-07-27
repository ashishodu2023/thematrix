from langgraph.types import Send

from matrix import story
from matrix.awareness import use_state
from matrix.config import config
from matrix.llm import character_act
from matrix.tools.agent_tools import detect_anomaly, scan_sector


def prepare_swarm(state: dict) -> dict:
    agents = list(state.get("agent_names") or config.default_agents)
    story.scene("AGENT SWARM")
    story.say(f"Deploying Agents: {', '.join(agents)}")
    story.beat("Send API fan-out — each Agent thinks independently")
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
    """Each Agent learns about peers from shared memory and acts alone."""
    agent = state["current_agent"]
    key = agent.strip().lower()
    sector = f"sector-{agent[0].lower()}1"
    scan = scan_sector(agent, state["city"], sector)
    anomaly = detect_anomaly(agent, state["anomaly"])

    with use_state(state):
        decision, patches = character_act(
            key,
            ["scan", "hunt", "contain", "observe"],
            (
                f"You are Agent {agent} in {state['city']}/{sector}. "
                f"Tool results: {scan}. {anomaly}. "
                "Choose your independent field action."
            ),
            state=state,
        )

    story.say(f"Agent {agent} → {state['city']}/{sector} action={decision.action}")
    story.speak_as(f"Agent {agent}", decision.speech)
    if decision.learned:
        story.beat(f"{agent} learned: {decision.learned}")

    return {
        "sectors_scanned": [f"{state['city']}/{sector}"],
        "agent_reports": [
            scan,
            anomaly,
            f"{agent}: action={decision.action} | {decision.speech}",
        ],
        "dialogue": [f"Agent {agent}: {decision.speech}"],
        "log": [f"[agent:{agent}] {decision.action} | {anomaly}"],
        **patches,
    }


def reconcile(state: dict) -> dict:
    spoon_seen = any("spoon" in r.lower() for r in state["agent_reports"])
    actions = list(state.get("character_actions") or [])
    story.scene("RECONCILE")
    story.say(
        f"{len(state['agent_reports'])} reports from "
        f"{len(state['sectors_scanned'])} sectors."
    )
    story.say(f"Spoon signal: {spoon_seen}")
    if actions:
        story.beat(f"Independent Agent actions: {len(actions)}")
    return {
        "agent_memory": [
            f"swarm: peers reported spoon={spoon_seen}; "
            f"actions={len(actions)}"
        ],
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
