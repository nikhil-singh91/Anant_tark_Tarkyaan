"""
Tarkyaan Autonomous Research Engine.
Orchestrates educational search, candidate extraction, multi-dimensional evaluation,
resource ranking, diversity curation, and persistence.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

from tarkyaan.events.event_bus import TarkyaanEvent, event_bus
from tarkyaan.memory.memory_manager import TarkyaanMemoryManager
from tarkyaan.models.enums import ResearchDepth, ResourceType, TaskType
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.learning import LearningPlan, LearningResource
from tarkyaan.models.planning import LearningTask
from tarkyaan.models.research import (
    CuratedResourceBundle,
    ResearchHistoryEntry,
    ResearchIntent,
    ResourceProvenance,
    SearchResultCandidate,
)
from tarkyaan.research.cache import ResearchCache
from tarkyaan.research.classifier import ResourceClassifier
from tarkyaan.research.curator import ResourceCurator
from tarkyaan.research.evaluator import ResourceEvaluator
from tarkyaan.research.extractor import ResourceExtractor
from tarkyaan.research.normalizer import URLNormalizer
from tarkyaan.research.providers.base import SearchOptions, SearchProvider
from tarkyaan.research.providers.mock import MockSearchProvider
from tarkyaan.research.providers.tavily import TavilySearchProvider
from tarkyaan.research.query_generator import QueryGenerator


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ResearchEngine:
    """
    Autonomous research and resource intelligence coordinator for Tarkyaan.
    Discovers, evaluates, and curates high-value learning materials tailored to learner needs.
    """

    def __init__(
        self,
        memory_manager: Optional[TarkyaanMemoryManager] = None,
        search_provider: Optional[SearchProvider] = None,
        cache: Optional[ResearchCache] = None
    ) -> None:
        self.memory = memory_manager or TarkyaanMemoryManager()
        self.cache = cache or ResearchCache()

        # Initialize provider (prefer Tavily if configured, fallback to Mock)
        if search_provider:
            self.provider = search_provider
        else:
            tavily = TavilySearchProvider()
            self.provider = tavily if tavily.is_configured() else MockSearchProvider()

    def set_provider(self, provider: SearchProvider) -> None:
        """Switch active search provider."""
        self.provider = provider

    def research_task(
        self,
        task: LearningTask,
        learner: LearnerProfile,
        plan: Optional[LearningPlan] = None,
        max_resources: int = 4,
        force_refresh: bool = False
    ) -> CuratedResourceBundle:
        """
        Conduct end-to-end research for an individual learning task.
        Attaches selected resource_ids to task.resource_ids and persists them.
        """
        concept_id = task.concept_id or task.topic_id or "general"

        event_bus.publish(
            TarkyaanEvent.RESEARCH_STARTED,
            payload={"task_id": task.task_id, "concept_id": concept_id, "provider": self.provider.name},
            learner_id=learner.learner_id
        )

        # 1. Resource Reuse Check (Section 30)
        if not force_refresh:
            existing = self.memory.list_resources_for_concept(concept_id)
            if len(existing) >= max_resources:
                # Reuse verified existing resources
                bundle = ResourceCurator.curate(
                    task_id=task.task_id,
                    concept_id=concept_id,
                    ranked_resources=existing,
                    task_type=task.task_type,
                    max_bundle_size=max_resources
                )
                task.resource_ids = bundle.all_resource_ids
                return bundle

        # 2. Derive Research Intent
        intent = ResearchIntent(
            learner_id=learner.learner_id,
            plan_id=plan.plan_id if plan else task.plan_id,
            task_id=task.task_id,
            concept_id=concept_id,
            learning_objective=task.objective or task.title,
            difficulty=task.difficulty,
            programming_language=learner.preferred_language if "python" in (learner.preferred_language or "").lower() or "c++" in (learner.preferred_language or "").lower() else None,
            depth=ResearchDepth.STANDARD
        )

        # 3. Generate Targeted Queries
        queries = QueryGenerator.generate_queries(intent=intent, task_type=task.task_type, max_queries=3)
        intent.generated_queries = queries

        # 4. Candidate Discovery (with cache checking)
        all_raw_candidates: List[SearchResultCandidate] = []
        for q in queries:
            resp = self.cache.get(q, self.provider.name)
            if not resp:
                resp = self.provider.search(q, SearchOptions(max_results=4, depth=intent.depth))
                if not resp.error and resp.candidates:
                    self.cache.set(q, self.provider.name, resp)

            all_raw_candidates.extend(resp.candidates)

        if not all_raw_candidates:
            event_bus.publish(
                TarkyaanEvent.RESEARCH_FAILED,
                payload={"task_id": task.task_id, "reason": "No search candidates discovered"},
                learner_id=learner.learner_id
            )
            return CuratedResourceBundle(task_id=task.task_id, concept_id=concept_id)

        # 5. Normalization & Deduplication
        unique_candidates = URLNormalizer.deduplicate(all_raw_candidates)

        # 6. Extraction, Classification, and Multi-Dimensional Evaluation
        evaluated_resources: List[LearningResource] = []
        for cand in unique_candidates:
            # Metadata Extraction & Untrusted Content Inspection
            meta = ResourceExtractor.extract(title=cand.title, snippet=cand.snippet, url=cand.url)
            res_type = ResourceClassifier.classify(url=cand.url, title=meta.title, snippet=meta.clean_snippet)

            # Evaluate 8 dimensions
            dim_scores, notes = ResourceEvaluator.evaluate(
                candidate=cand,
                intent=intent,
                learner=learner,
                task_type=task.task_type,
                resource_type=res_type
            )

            # Build Provenance Audit Trail
            provenance = ResourceProvenance(
                discovery_queries=cand.metadata.get("discovery_queries", [cand.discovery_query]),
                discovery_provider=cand.provider,
                retrieval_timestamp=_utc_now(),
                canonical_url=cand.url,
                is_content_fetched=False,
                extraction_method="metadata_and_snippet",
                evaluator_version="1.0.0",
                ranking_version="1.0.0",
                selection_reason="Evaluated against task objectives and learner profile."
            )

            res = LearningResource(
                title=meta.title,
                url=cand.url,
                resource_type=res_type.value,
                domain=meta.domain,
                provider=cand.provider,
                description=meta.clean_snippet,
                topic_id=concept_id,
                concept_ids=[concept_id],
                task_ids=[task.task_id],
                difficulty=task.difficulty,
                language=learner.preferred_language or "en",
                duration_minutes=int(round(meta.estimated_duration_minutes)),
                relevance_score=dim_scores.relevance,
                authority_score=dim_scores.authority,
                quality_score=dim_scores.quality,
                learner_fit_score=dim_scores.learner_fit,
                freshness_score=dim_scores.freshness,
                usefulness_score=dim_scores.practical_usefulness,
                confidence=dim_scores.confidence,
                provenance=provenance,
                evaluation_notes=notes,
                discovered_at=cand.discovered_at
            )
            evaluated_resources.append(res)

        # 7. Deterministic Ranking
        from tarkyaan.research.ranker import ResourceRanker
        ranked_resources = ResourceRanker.rank_resources(evaluated_resources)

        # 8. Diverse Bundle Curation
        bundle = ResourceCurator.curate(
            task_id=task.task_id,
            concept_id=concept_id,
            ranked_resources=ranked_resources,
            task_type=task.task_type,
            max_bundle_size=max_resources
        )

        # 9. Persistence of Selected & Discovered Resources
        for r in ranked_resources:
            self.memory.save_resource(r)

        # Record Research History Audit Log
        history_entry = ResearchHistoryEntry(
            learner_id=learner.learner_id,
            task_id=task.task_id,
            concept_id=concept_id,
            query=queries[0] if queries else "",
            provider=self.provider.name,
            status="success",
            discovered_count=len(unique_candidates),
            selected_count=len(bundle.all_resource_ids),
            selected_resource_ids=bundle.all_resource_ids,
            timestamp=_utc_now()
        )
        self.memory.save_research_history(history_entry)

        # 10. Attach to LearningTask
        task.resource_ids = bundle.all_resource_ids

        event_bus.publish(
            TarkyaanEvent.RESEARCH_COMPLETED,
            payload={"task_id": task.task_id, "selected_count": len(bundle.all_resource_ids)},
            learner_id=learner.learner_id
        )

        return bundle

    def research_plan(
        self,
        plan: LearningPlan,
        learner: LearnerProfile,
        max_resources_per_task: int = 3,
        force_refresh: bool = False
    ) -> LearningPlan:
        """
        Execute research across an entire LearningPlan.
        Researches only tasks that require external learning resources, reusing materials across shared concepts.
        """
        # Tasks needing resources
        research_eligible_types = {
            TaskType.LEARN,
            TaskType.UNDERSTAND,
            TaskType.PRACTICE,
            TaskType.SOLVE,
            TaskType.APPLY,
            TaskType.EXPLAIN,
        }

        for phase in plan.phases:
            for task in phase.tasks:
                if task.task_type in research_eligible_types:
                    self.research_task(
                        task=task,
                        learner=learner,
                        plan=plan,
                        max_resources=max_resources_per_task,
                        force_refresh=force_refresh
                    )

        # Sync top-level task list in plan
        all_phase_tasks = [t for p in plan.phases for t in p.tasks]
        plan.tasks = all_phase_tasks

        # Persist updated plan
        self.memory.save_learning_plan(plan)
        return plan
