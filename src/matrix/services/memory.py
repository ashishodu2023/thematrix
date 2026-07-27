from langgraph.checkpoint.redis import RedisSaver

from matrix.models import MatrixSession, PreviousLife
from matrix.services.redis_client import REDIS_URL, redis_client


def build_checkpointer():
    """
    Operator-side durable checkpointer (outside the Matrix).

    Do not wrap in `with` at module level — exiting the context
    closes Redis before graph.invoke() runs.
    """
    saver = RedisSaver.from_conn_string(REDIS_URL)
    checkpointer = saver.__enter__()
    checkpointer.setup()
    return checkpointer


class SessionMemory:
    """Cross-cycle memory of humans who have jacked in before."""

    PREFIX = "matrix:session"

    @classmethod
    def save(cls, session: MatrixSession) -> None:
        key = f"{cls.PREFIX}:{session.human_id}"
        redis_client.set(key, session.model_dump_json())

    @classmethod
    def load(cls, human_id: str) -> MatrixSession:
        key = f"{cls.PREFIX}:{human_id}"
        value = redis_client.get(key)
        if value is None:
            return MatrixSession(human_id=human_id)
        return MatrixSession.model_validate_json(value)

    @classmethod
    def record_life(cls, human_id: str, life: PreviousLife) -> MatrixSession:
        session = cls.load(human_id)
        session.lives.append(life)
        if life.pill_choice == "red":
            session.awakened_count += 1
        cls.save(session)
        return session

    @classmethod
    def remember_agents(cls, human_id: str, observations: list[str]) -> MatrixSession:
        """Persist multi-agent learning so next cycle brains still know peers."""
        session = cls.load(human_id)
        for obs in observations:
            text = (obs or "").strip()
            if text and text not in session.agent_knowledge:
                session.agent_knowledge.append(text)
        # Cap growth under continuous reincarnation
        session.agent_knowledge = session.agent_knowledge[-200:]
        cls.save(session)
        return session

    @classmethod
    def apply_sticky(cls, human_id: str, state: dict) -> MatrixSession:
        """Permanent branch flags from choices this life."""
        session = cls.load(human_id)
        flags = dict(session.sticky_flags or {})
        if state.get("bug_choice") == "refuse" or state.get("bug_implanted"):
            flags["bug_implanted"] = True
        if state.get("trust_choice") == "walk":
            flags["walked_from_trinity"] = True
        if state.get("trust_choice") == "trust":
            flags["trusted_trinity"] = True
        if state.get("steak_choice") == "steak":
            flags["cypher_deal"] = True
        if state.get("code_choice") == "accept":
            flags["saw_code"] = True
        if state.get("key_choice") == "take_key":
            flags["took_key"] = True
        if state.get("key_choice") == "refuse_key":
            flags["refused_key"] = True
        if (state.get("sticky_flags") or {}).get("defied_merovingian"):
            flags["defied_merovingian"] = True
        session.sticky_flags = flags
        cls.save(session)
        return session
