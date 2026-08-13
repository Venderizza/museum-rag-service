from dataclasses import dataclass
from app.domain.enums import MessageRole


@dataclass(slots=True)
class ChatMessage:
    role: MessageRole
    content: str
