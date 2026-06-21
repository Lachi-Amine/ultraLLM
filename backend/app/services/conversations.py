from dataclasses import dataclass, field
from uuid import UUID, uuid4

from ..schemas import ChatMessage


@dataclass
class Conversation:
    id: UUID = field(default_factory=uuid4)
    messages: list[ChatMessage] = field(default_factory=list)


class ConversationStore:
    def __init__(self) -> None:
        self._conversations: dict[UUID, Conversation] = {}

    def get_or_create(self, conversation_id: UUID | None) -> Conversation:
        if conversation_id is not None and conversation_id in self._conversations:
            return self._conversations[conversation_id]
        conversation = Conversation(id=conversation_id or uuid4())
        self._conversations[conversation.id] = conversation
        return conversation
