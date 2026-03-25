"""
Student Memory Module
Stores and retrieves student identity, academic context, and conversation history.
Supports entity memory, summary memory, and optional vector memory.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Persistent memory storage directory
MEMORY_DIR = Path(__file__).parent.parent.parent / "memory_store"
MEMORY_DIR.mkdir(exist_ok=True)


class StudentEntity:
    """Represents a student's profile/identity."""
    def __init__(self):
        self.name: Optional[str] = None
        self.student_id: Optional[str] = None
        self.program: Optional[str] = None   # BTech, MBA, MSc, PhD
        self.year: Optional[int] = None       # 1, 2, 3, 4
        self.department: Optional[str] = None
        self.nationality: str = "domestic"    # domestic or international
        self.email: Optional[str] = None
        self.interests: List[str] = []        # course interests
        self.completed_courses: List[str] = []
        self.ongoing_issues: List[str] = []
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = datetime.now().isoformat()

    def update(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        self.updated_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "student_id": self.student_id,
            "program": self.program,
            "year": self.year,
            "department": self.department,
            "nationality": self.nationality,
            "email": self.email,
            "interests": self.interests,
            "completed_courses": self.completed_courses,
            "ongoing_issues": self.ongoing_issues,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "StudentEntity":
        entity = cls()
        for key, value in data.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        return entity

    def get_context_string(self) -> str:
        """Format student info as a context string for the LLM."""
        parts = []
        if self.name:
            parts.append(f"Student Name: {self.name}")
        if self.program:
            parts.append(f"Program: {self.program}")
        if self.year:
            parts.append(f"Year: {self.year}")
        if self.department:
            parts.append(f"Department: {self.department}")
        if self.nationality:
            parts.append(f"Nationality: {self.nationality}")
        if self.interests:
            parts.append(f"Course Interests: {', '.join(self.interests)}")
        if self.completed_courses:
            parts.append(f"Completed Courses: {', '.join(self.completed_courses)}")
        if self.ongoing_issues:
            parts.append(f"Ongoing Issues: {', '.join(self.ongoing_issues)}")
        return "\n".join(parts) if parts else "No student profile yet."


class ConversationMemory:
    """Stores and summarizes multi-turn conversation history."""

    def __init__(self, session_id: str, max_turns: int = 20, summary_threshold: int = 10):
        self.session_id = session_id
        self.max_turns = max_turns
        self.summary_threshold = summary_threshold
        self.messages: List[Dict] = []
        self.summary: str = ""
        self.turn_count: int = 0

    def add_message(self, role: str, content: str):
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
        })
        if role == "user":
            self.turn_count += 1

        # Trim if too long (keep last max_turns exchanges)
        if len(self.messages) > self.max_turns * 2:
            # Summarize older messages
            cutoff = len(self.messages) - self.max_turns * 2
            old_messages = self.messages[:cutoff]
            self.summary = self._create_summary(old_messages)
            self.messages = self.messages[cutoff:]

    def _create_summary(self, messages: List[Dict]) -> str:
        """Create a text summary of old messages."""
        if not messages:
            return ""
        topics = []
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"][:100]
                topics.append(f"Student asked: {content}")
        summary = "Earlier in this conversation: " + " | ".join(topics[:5])
        return summary

    def get_history_for_llm(self) -> List[Dict]:
        """Return conversation history in LLM-compatible format."""
        history = []
        if self.summary:
            # Inject summary as a system-like context
            history.append({
                "role": "assistant",
                "content": f"[Previous conversation summary: {self.summary}]"
            })
        for msg in self.messages:
            history.append({"role": msg["role"], "content": msg["content"]})
        return history

    def get_recent_context(self, n: int = 6) -> str:
        """Get last n messages as a string."""
        recent = self.messages[-n:]
        lines = []
        for msg in recent:
            role = "Student" if msg["role"] == "user" else "Assistant"
            lines.append(f"{role}: {msg['content'][:200]}")
        return "\n".join(lines)


class StudentMemoryManager:
    """
    Top-level memory manager combining entity memory + conversation memory.
    Can optionally persist to disk.
    """

    def __init__(self, session_id: str, persist: bool = True):
        self.session_id = session_id
        self.persist = persist
        self.entity = StudentEntity()
        self.conversation = ConversationMemory(session_id)
        self._memory_path = MEMORY_DIR / f"{session_id}.json"

        if persist and self._memory_path.exists():
            self.load()

    def extract_and_update_student_info(self, user_message: str):
        """
        Simple rule-based extraction to update student profile from conversation.
        For production, this would use an LLM-based entity extractor.
        """
        msg_lower = user_message.lower()

        # Program detection
        program_map = {
            "btech": "BTech", "b.tech": "BTech",
            "mba": "MBA",
            "msc": "MSc", "m.sc": "MSc",
            "phd": "PhD", "ph.d": "PhD",
        }
        for key, prog in program_map.items():
            if key in msg_lower:
                self.entity.update(program=prog)
                break

        # Year detection
        import re
        year_match = re.search(r"\b([1-4])(st|nd|rd|th)?\s*year\b", msg_lower)
        if year_match:
            self.entity.update(year=int(year_match.group(1)))

        # Nationality
        if "international" in msg_lower or "visa" in msg_lower or "frro" in msg_lower:
            self.entity.update(nationality="international")

        # Name extraction (simple "my name is X" or "I am X")
        name_match = re.search(r"(?:my name is|i am|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)", user_message)
        if name_match and not self.entity.name:
            self.entity.update(name=name_match.group(1))

        # Department detection
        dept_keywords = {
            "computer science": "Computer Science",
            "data science": "Data Science",
            "mathematics": "Mathematics",
            "management": "Management",
            "mba": "Management",
        }
        for key, dept in dept_keywords.items():
            if key in msg_lower:
                self.entity.update(department=dept)
                break

        if self.persist:
            self.save()

    def add_user_message(self, content: str):
        self.conversation.add_message("user", content)
        self.extract_and_update_student_info(content)

    def add_assistant_message(self, content: str):
        self.conversation.add_message("assistant", content)
        if self.persist:
            self.save()

    def get_full_context(self) -> Dict:
        return {
            "student_profile": self.entity.to_dict(),
            "conversation_history": self.conversation.get_history_for_llm(),
            "recent_context": self.conversation.get_recent_context(),
            "student_context_string": self.entity.get_context_string(),
        }

    def save(self):
        """Persist memory to disk."""
        try:
            data = {
                "session_id": self.session_id,
                "entity": self.entity.to_dict(),
                "messages": self.conversation.messages[-50:],  # Save last 50
                "summary": self.conversation.summary,
                "turn_count": self.conversation.turn_count,
            }
            with open(self._memory_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save memory: {e}")

    def load(self):
        """Load memory from disk."""
        try:
            with open(self._memory_path, "r") as f:
                data = json.load(f)
            self.entity = StudentEntity.from_dict(data.get("entity", {}))
            self.conversation.messages = data.get("messages", [])
            self.conversation.summary = data.get("summary", "")
            self.conversation.turn_count = data.get("turn_count", 0)
        except Exception as e:
            logger.error(f"Failed to load memory: {e}")

    def clear(self):
        """Clear all memory for this session."""
        self.entity = StudentEntity()
        self.conversation = ConversationMemory(self.session_id)
        if self._memory_path.exists():
            self._memory_path.unlink()


# Session registry
_sessions: Dict[str, StudentMemoryManager] = {}


def get_memory_manager(session_id: str) -> StudentMemoryManager:
    """Get or create a memory manager for a session."""
    if session_id not in _sessions:
        _sessions[session_id] = StudentMemoryManager(session_id)
    return _sessions[session_id]


def clear_session(session_id: str):
    """Clear and remove a session."""
    if session_id in _sessions:
        _sessions[session_id].clear()
        del _sessions[session_id]
