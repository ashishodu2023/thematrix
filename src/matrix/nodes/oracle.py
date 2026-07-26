from langgraph.types import interrupt

from matrix import story
from matrix.characters import PERSONAS
from matrix.llm import speak
from matrix.world import LOCATIONS


def oracle_question(state: dict) -> dict:
    """HITL — Operator asks the Oracle a question."""
    story.scene("BEFORE THE ORACLE")
    story.say("The kitchen door is open. What will you ask?")

    question = interrupt(
        {
            "kind": "oracle_question",
            "message": "Ask the Oracle a question (free text).",
            "human_id": state["human_id"],
            "hint": 'Example: Am I the One?',
        }
    )
    text = str(question).strip() or "Am I the One?"
    story.say(f"You ask: {text}")
    return {
        "oracle_question": text,
        "pending_decision": "oracle_question",
        "events": [f"oracle_question:{text}"],
        "log": [f"[oracle_q] {text}"],
    }


def oracle_speak(state: dict) -> dict:
    """Oracle answers via Ollama."""
    loc = LOCATIONS["oracle_apartment"]
    story.scene("THE ORACLE")
    story.say(f"{loc.name}: {loc.description}")

    prophecy = speak(
        PERSONAS["oracle"],
        (
            f"The human asks: '{state.get('oracle_question') or 'Am I the One?'}'. "
            f"Anomaly in the city: {state['anomaly']}. "
            f"They have {state['previous_lives']} prior lives. "
            "Answer cryptically in 1-2 sentences."
        ),
    )
    story.speak_as("Oracle", prophecy)

    return {
        "location": loc.id,
        "scene": "oracle",
        "oracle_prophecy": prophecy,
        "pending_decision": "",
        "dialogue": [f"Oracle: {prophecy}"],
        "events": ["oracle:spoke"],
        "log": [f"[oracle] {prophecy}"],
        "locations_visited": [loc.id],
    }
