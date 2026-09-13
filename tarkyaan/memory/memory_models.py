"""
Tarkyaan Independent Memory Models.
Defines structured memory units with epistemic status, provenance, and access metadata.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tarkyaan.models.enums import EpistemicStatus, MemorySource, MemoryType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MemoryItem(BaseModel):
    """
    A single typed memory record stored in Tarkyaan's persistent memory system.
    Strictly isolates facts from inferences, tracks importance, confidence, and provenance.
    """
    memory_id: str = Field(
        default_factory=lambda: f"mem_{uuid.uuid4().hex[:12]}",
        description="Unique identifier for the memory item"
    )
    learner_id: str = Field(..., description="Foreign key ensuring strict learner isolation")
    memory_type: MemoryType = Field(..., description="Semantic, knowledge state, episodic, goal, etc.")
    key: str = Field(..., min_length=1, max_length=120, description="Descriptor key (e.g. 'preferred_ide', 'active_gap')")
    content: str = Field(..., description="Natural language or human-readable representation")
    structured_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="JSON serializable dictionary representing structured payload"
    )
    source: MemorySource = Field(
        default=MemorySource.USER_EXPLICIT,
        description="Provenance of the remembered information"
    )
    epistemic_status: EpistemicStatus = Field(
        default=EpistemicStatus.FACT,
        description="FACT (verified by user/system) or INFERENCE (deduced by model)"
    )
    importance: int = Field(default=3, ge=1, le=5, description="1 (trivial) to 5 (critical)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Belief certainty in [0.0, 1.0]")
    topic_id: Optional[str] = Field(default=None, description="Associated concept if topic-specific")
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)
    last_accessed_at: Optional[datetime] = None
    access_count: int = Field(default=0, ge=0)

    def access(self) -> None:
        """Mark memory as accessed and increment counter."""
        self.last_accessed_at = _utc_now()
        self.access_count += 1
