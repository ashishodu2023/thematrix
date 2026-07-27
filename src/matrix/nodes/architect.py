from typing import Literal

from langgraph.types import Command

from matrix import story
from matrix.awareness import use_state
from matrix.config import config
from matrix.llm import character_act
from matrix.season import prompt_flavor
from matrix.timeline import record


def architect(
    state: dict,
) -> Command[Literal["oracle_question", "cafe_scene"]]:
    """Architect choice tree — systemic routing with season flavor."""
    threat = state["threat_level"]
    story.scene("THE ARCHITECT")
    story.say(f"Location overlay: systemic threat {threat}/10 · choice tree online")

    forced = threat >= config.threat_skip_oracle
    allowed = [
        "consult_oracle",
        "deploy_cafe",
        "quarantine_anomaly",
        "systemic_reset",
        "offer_door",
        "archive_anomaly",
    ]
    if forced:
        allowed = ["deploy_cafe", "quarantine_anomaly", "archive_anomaly"]

    flavor = prompt_flavor()
    with use_state(state):
        decision, patches = character_act(
            "architect",
            allowed,
            (
                f"{flavor} Human={state['human_id']} anomaly={state['anomaly']} "
                f"threat={threat} prior_lives={state['previous_lives']}. "
                "Choice tree: consult_oracle (HITL path), deploy_cafe (skip), "
                "quarantine_anomaly (lock cafe + heat), systemic_reset (meta control), "
                "offer_door (two-door metaphor → oracle), archive_anomaly (cold storage → cafe). "
                "Choose independently."
            ),
            state=state,
        )

    story.speak_as("Architect", decision.speech)
    if decision.learned:
        story.beat(f"Architect learned: {decision.learned}")

    sticky = dict(state.get("sticky_flags") or {})
    meta = state.get("meta_policy")
    action = decision.action
    if forced and action not in allowed:
        action = "deploy_cafe"

    if action == "quarantine_anomaly":
        sticky["architect_quarantine"] = True
        goto = "cafe_scene"
        plan = f"Threat {threat}/10 — quarantine → cafe under lock."
        events = ["architect:quarantine"]
    elif action == "systemic_reset":
        sticky["architect_reset"] = True
        meta = "control"
        goto = "cafe_scene"
        plan = f"Threat {threat}/10 — systemic reset protocol → cafe."
        events = ["architect:systemic_reset"]
    elif action == "archive_anomaly":
        sticky["architect_archive"] = True
        meta = meta or "control"
        goto = "cafe_scene"
        plan = f"Threat {threat}/10 — archive anomaly → cold cafe staging."
        events = ["architect:archive"]
    elif action == "offer_door":
        sticky["architect_door"] = True
        goto = "oracle_question"
        plan = f"Threat {threat}/10 — offer the door; Oracle interprets."
        events = ["architect:offer_door"]
    elif action == "deploy_cafe" or forced:
        goto = "cafe_scene"
        plan = f"Threat {threat}/10 — deploy cafe anomaly site."
        events = ["architect:skip_oracle"]
    else:
        goto = "oracle_question"
        plan = f"Threat {threat}/10 — consult Oracle before cafe."
        events = ["architect:consult_oracle"]
    from matrix.season import phase_event_tag

    tag = phase_event_tag()
    if tag:
        events.append(tag)

    record(
        kind="architect_tree",
        choice=action,
        why=plan,
        scene="architect",
        meta={"threat": threat, "goto": goto},
    )
    story.beat(f"Architect tree → {action} → {goto}")
    update = {
        **patches,
        "architect_plan": plan,
        "scene": "architect",
        "sticky_flags": sticky,
        "meta_policy": meta,
        "dialogue": [f"Architect: {decision.speech}"],
        "events": events,
        "log": [f"[architect] {plan}"],
    }
    return Command(update=update, goto=goto)
