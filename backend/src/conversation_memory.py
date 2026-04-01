"""Conversation memory for multi-turn chat sessions"""

from datetime import datetime, timedelta
from collections import OrderedDict
from src.logger import get_logger
import threading
import uuid

logger = get_logger(__name__)


class ConversationTurn:
    """A single turn in a conversation"""

    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.utcnow()

    def to_dict(self):
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }


class ConversationSession:
    """A conversation session with history"""

    def __init__(self, session_id: str, max_turns: int = 50, system_prompt: str = None):
        self.session_id = session_id
        self.max_turns = max_turns
        self.turns = []
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.metadata = {}

        if system_prompt:
            self.turns.append(ConversationTurn("system", system_prompt))

    def add_turn(self, role: str, content: str):
        """Add a turn to the conversation"""
        self.turns.append(ConversationTurn(role, content))
        self.updated_at = datetime.utcnow()

        # Trim old turns if exceeding max, but keep system prompt
        if len(self.turns) > self.max_turns:
            system_turns = [t for t in self.turns if t.role == "system"]
            non_system = [t for t in self.turns if t.role != "system"]
            self.turns = system_turns + non_system[-(self.max_turns - len(system_turns)):]

    def get_context_window(self, max_tokens_estimate: int = 2048) -> list:
        """Get recent turns that fit within a token budget

        Uses a rough estimate of 4 chars per token.
        """
        result = []
        total_chars = 0
        char_budget = max_tokens_estimate * 4

        for turn in reversed(self.turns):
            turn_chars = len(turn.content)
            if total_chars + turn_chars > char_budget and result:
                break
            result.insert(0, turn)
            total_chars += turn_chars

        return result

    def build_prompt(self, max_tokens_estimate: int = 2048) -> str:
        """Build a formatted prompt string from conversation history"""
        turns = self.get_context_window(max_tokens_estimate)
        parts = []
        for turn in turns:
            if turn.role == "system":
                parts.append(f"[INST] <<SYS>>\n{turn.content}\n<</SYS>>")
            elif turn.role == "user":
                parts.append(f"[INST] {turn.content} [/INST]")
            elif turn.role == "assistant":
                parts.append(turn.content)
        return "\n".join(parts)

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "turns": [t.to_dict() for t in self.turns],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "turn_count": len(self.turns),
        }


class ConversationMemory:
    """Manage multiple conversation sessions with automatic cleanup"""

    def __init__(self, max_sessions: int = 1000, session_ttl_hours: int = 24, max_turns: int = 50):
        self.max_sessions = max_sessions
        self.session_ttl = timedelta(hours=session_ttl_hours)
        self.max_turns = max_turns
        self.sessions = OrderedDict()
        self._lock = threading.Lock()

    def create_session(self, system_prompt: str = None) -> str:
        """Create a new conversation session and return its ID"""
        with self._lock:
            self._cleanup_expired()
            session_id = str(uuid.uuid4())
            self.sessions[session_id] = ConversationSession(
                session_id=session_id,
                max_turns=self.max_turns,
                system_prompt=system_prompt,
            )
            logger.info(f"Created conversation session: {session_id}")
            return session_id

    def get_session(self, session_id: str) -> ConversationSession:
        """Retrieve a session by ID"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session and (datetime.utcnow() - session.updated_at) > self.session_ttl:
                del self.sessions[session_id]
                logger.info(f"Session expired: {session_id}")
                return None
            return session

    def add_exchange(self, session_id: str, user_message: str, assistant_response: str):
        """Add a user/assistant exchange to a session"""
        session = self.get_session(session_id)
        if not session:
            return False
        session.add_turn("user", user_message)
        session.add_turn("assistant", assistant_response)
        return True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        with self._lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Deleted session: {session_id}")
                return True
            return False

    def list_sessions(self) -> list:
        """List all active sessions"""
        with self._lock:
            self._cleanup_expired()
            return [
                {
                    "session_id": sid,
                    "turn_count": len(s.turns),
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                }
                for sid, s in self.sessions.items()
            ]

    def _cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.utcnow()
        expired = [
            sid for sid, s in self.sessions.items()
            if (now - s.updated_at) > self.session_ttl
        ]
        for sid in expired:
            del self.sessions[sid]

        # Evict oldest if over capacity
        while len(self.sessions) > self.max_sessions:
            self.sessions.popitem(last=False)


conversation_memory = ConversationMemory()
