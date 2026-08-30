from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class Message:
    role: str
    content: str
    created_at: datetime | None


@dataclass(frozen=True)
class Conversation:
    id: str
    title: str
    created_at: datetime | None
    messages: tuple[Message, ...]

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class Hole:
    id: str
    name: str
    conversation_ids: list[str]
    message_count: int
    last_active: datetime | None
    last_researched_at: datetime | None = None

    @property
    def stale(self) -> bool:
        if self.last_researched_at is None:
            return True
        if self.last_active is None:
            return False
        return self.last_researched_at < self.last_active


@dataclass
class Insight:
    hole_id: str
    content: str
    sources: list[str]
    created_at: datetime


@dataclass
class PlanItem:
    hole_id: str
    hole_name: str
    action: str
    sources: list[str]
    score: float


@dataclass
class Plan:
    date: str
    items: list[PlanItem]
    committed: bool = False


@dataclass
class State:
    conversations: dict[str, Conversation] = field(default_factory=dict)
    holes: dict[str, Hole] = field(default_factory=dict)
    insights: list[Insight] = field(default_factory=list)
    plan: Plan | None = None
