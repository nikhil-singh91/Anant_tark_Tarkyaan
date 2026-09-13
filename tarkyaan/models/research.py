"""Research Models and Schemas for Tarkyaan.

Defines schemas for research intents, search candidates, multi-dimensional evaluation,
provenance metadata, curated resource bundles, and research history entries.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator

from tarkyaan.models.enums import ResearchDepth, ResourceType


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResourceProvenance(BaseModel):
    """Provenance and audit trail for a discovered resource."""
    provider: str = Field(default="mock", description="Search provider that discovered this resource")
    discovery_provider: str = Field(default="mock")
    query: str = Field(default="", description="Search query that surfaced this resource")
    discovery_queries: List[str] = Field(default_factory=list)
    search_rank: int = Field(default=1, ge=1, description="Rank in raw search engine results")
    retrieved_at: datetime = Field(default_factory=_utc_now)
    retrieval_timestamp: Optional[datetime] = None
    canonical_url: str = ""
    is_content_fetched: bool = False
    extraction_method: str = "metadata_and_snippet"
    evaluator_version: str = "1.0.0"
    ranking_version: str = "1.0.0"
    selection_reason: str = ""
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_provenance_aliases(self) -> "ResourceProvenance":
        if self.discovery_provider and not self.provider:
            self.provider = self.discovery_provider
        elif self.provider and not self.discovery_provider:
            self.discovery_provider = self.provider
        if self.discovery_queries and not self.query:
            self.query = self.discovery_queries[0]
        elif self.query and not self.discovery_queries:
            self.discovery_queries = [self.query]
        if self.retrieval_timestamp and not self.retrieved_at:
            self.retrieved_at = self.retrieval_timestamp
        elif self.retrieved_at and not self.retrieval_timestamp:
            self.retrieval_timestamp = self.retrieved_at
        return self


class SearchResultCandidate(BaseModel):
    """Raw result candidate discovered from a search provider before full extraction & scoring."""
    candidate_id: str = Field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:8]}")
    title: str
    url: str
    snippet: str
    domain: str = ""
    source_domain: str = ""
    provider: str = "mock"
    raw_score: float = 0.0
    rank_from_provider: int = 1
    published_date: Optional[str] = None
    query_origin: str = ""
    discovery_query: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=_utc_now)

    @model_validator(mode="after")
    def sync_aliases(self) -> "SearchResultCandidate":
        if self.source_domain and not self.domain:
            self.domain = self.source_domain
        elif self.domain and not self.source_domain:
            self.source_domain = self.domain
        if self.discovery_query and not self.query_origin:
            self.query_origin = self.discovery_query
        elif self.query_origin and not self.discovery_query:
            self.discovery_query = self.query_origin
        return self



class ResourceDimensionScores(BaseModel):
    """Multi-dimensional evaluation breakdown for an educational resource."""
    relevance: float = Field(ge=0.0, le=1.0, description="Semantic and topical alignment")
    authority: float = Field(ge=0.0, le=1.0, description="Institutional authority & source credibility")
    quality: float = Field(ge=0.0, le=1.0, description="Clarity, structure, completeness")
    difficulty_fit: float = Field(ge=0.0, le=1.0, description="Calibration to learner target difficulty")
    learner_fit: float = Field(ge=0.0, le=1.0, description="Adaptation to learner style and pace")
    freshness: float = Field(ge=0.0, le=1.0, description="Recency and technological currency")
    practical_usefulness: float = Field(ge=0.0, le=1.0, description="Actionability, examples, problem sets")
    confidence: float = Field(ge=0.0, le=1.0, description="Evaluator certainty score")
    overall: float = Field(default=0.0, ge=0.0, le=1.0, description="Weighted composite rating")


class ResearchIntent(BaseModel):
    """Structured research intention generated from a learning task or topic."""
    intent_id: str = Field(default_factory=lambda: f"intent_{uuid.uuid4().hex[:8]}")
    learner_id: Optional[str] = None
    plan_id: Optional[str] = None
    task_id: Optional[str] = None
    concept_id: Optional[str] = None
    concept_name: str = ""
    learning_objective: str = ""
    programming_language: Optional[str] = None
    difficulty: int = 2
    task_type: Optional[str] = None
    depth: ResearchDepth = ResearchDepth.STANDARD
    learner_level: Optional[str] = None
    preferred_types: List[ResourceType] = Field(default_factory=list)
    avoid_domains: List[str] = Field(default_factory=list)
    generated_queries: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_utc_now)

    @model_validator(mode="after")
    def sync_concept_name(self) -> "ResearchIntent":
        if not self.concept_name and self.concept_id:
            self.concept_name = self.concept_id.replace("_", " ")
        elif not self.concept_id and self.concept_name:
            self.concept_id = self.concept_name.lower().replace(" ", "_")
        return self



class CuratedResourceBundle(BaseModel):
    """Curated bundle of differentiated resources selected for an atomic learning task."""
    bundle_id: str = Field(default_factory=lambda: f"bundle_{uuid.uuid4().hex[:8]}")
    task_id: Optional[str] = None
    concept_id: Optional[str] = None
    primary_resource_id: Optional[str] = None
    supporting_resource_ids: List[str] = Field(default_factory=list)
    practice_resource_ids: List[str] = Field(default_factory=list)
    reference_resource_ids: List[str] = Field(default_factory=list)
    all_resource_ids: List[str] = Field(default_factory=list)
    selection_rationales: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=_utc_now)


class ResearchHistoryEntry(BaseModel):
    """Historical record of an autonomous research inquiry."""
    history_id: str = Field(default_factory=lambda: f"rh_{uuid.uuid4().hex[:8]}")
    learner_id: str
    task_id: Optional[str] = None
    concept_id: Optional[str] = None
    query: str
    provider: str
    status: str
    discovered_count: int = 0
    selected_count: int = 0
    selected_resource_ids: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_utc_now)
