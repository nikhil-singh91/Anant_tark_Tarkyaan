"""
Educational Resource Curator.
Synthesizes balanced, diverse bundles (Primary, Supporting, Practice, Reference)
with factual, explainable selection rationales.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from tarkyaan.models.enums import ResourceType, TaskType
from tarkyaan.models.learning import LearningResource
from tarkyaan.models.research import CuratedResourceBundle


class ResourceCurator:
    """
    Curates a non-redundant, complementary bundle of resources for an atomic learning task.
    Prevents link dumps by limiting items and balancing resource types.
    """

    @classmethod
    def curate(
        cls,
        task_id: str,
        concept_id: str,
        ranked_resources: List[LearningResource],
        task_type: TaskType = TaskType.LEARN,
        max_bundle_size: int = 4
    ) -> CuratedResourceBundle:
        """
        Assemble a curated resource bundle with categorized roles and selection rationales.
        """
        bundle = CuratedResourceBundle(
            task_id=task_id,
            concept_id=concept_id
        )

        if not ranked_resources:
            return bundle

        rationales: Dict[str, str] = {}

        # 1. Select Primary Resource
        # If task is practice, prefer coding problem; otherwise prefer docs/tutorial
        primary: Optional[LearningResource] = None
        if task_type in (TaskType.PRACTICE, TaskType.SOLVE):
            practice_candidates = [r for r in ranked_resources if r.resource_type in (ResourceType.CODING_PROBLEM.value, ResourceType.EXERCISE.value)]
            primary = practice_candidates[0] if practice_candidates else ranked_resources[0]
        else:
            doc_candidates = [r for r in ranked_resources if r.resource_type in (ResourceType.OFFICIAL_DOCS.value, ResourceType.TUTORIAL.value, ResourceType.INTERACTIVE.value)]
            primary = doc_candidates[0] if doc_candidates else ranked_resources[0]

        bundle.primary_resource_id = primary.resource_id
        rationales[primary.resource_id] = (
            f"Primary Resource: Highest rated ({primary.overall_score:.2f}) {primary.resource_type.replace('_', ' ')} "
            f"from {primary.domain or 'source'} with authority score {primary.authority_score:.2f}."
        )

        # 2. Select Supporting / Visual Resource
        supporting = [
            r for r in ranked_resources
            if r.resource_id != primary.resource_id and
            r.resource_type in (ResourceType.INTERACTIVE.value, ResourceType.VIDEO.value, ResourceType.TUTORIAL.value, ResourceType.ARTICLE.value)
        ]
        if supporting:
            s_res = supporting[0]
            bundle.supporting_resource_ids.append(s_res.resource_id)
            rationales[s_res.resource_id] = (
                f"Supporting Explanation: Provides complementary intuition and examples ({s_res.resource_type})."
            )

        # 3. Select Practice / Hands-on Resource
        practice = [
            r for r in ranked_resources
            if r.resource_id != primary.resource_id and
            r.resource_id not in bundle.supporting_resource_ids and
            r.resource_type in (ResourceType.CODING_PROBLEM.value, ResourceType.EXERCISE.value)
        ]
        if practice:
            p_res = practice[0]
            bundle.practice_resource_ids.append(p_res.resource_id)
            rationales[p_res.resource_id] = (
                f"Practice Resource: Targeted problem set from {p_res.domain} to verify and reinforce application."
            )

        # 4. Select Reference / Deeper Insight Resource
        reference = [
            r for r in ranked_resources
            if r.resource_id != primary.resource_id and
            r.resource_id not in bundle.supporting_resource_ids and
            r.resource_id not in bundle.practice_resource_ids and
            r.resource_type in (ResourceType.REFERENCE.value, ResourceType.RESEARCH_PAPER.value, ResourceType.OFFICIAL_DOCS.value)
        ]
        if reference and len(bundle.supporting_resource_ids) + len(bundle.practice_resource_ids) < max_bundle_size - 1:
            ref_res = reference[0]
            bundle.reference_resource_ids.append(ref_res.resource_id)
            rationales[ref_res.resource_id] = (
                f"Deeper Reference: Academic or formal specification from {ref_res.domain} for advanced inquiry."
            )

        # Collect all selected resource IDs preserving order
        all_ids = [primary.resource_id]
        all_ids.extend(bundle.supporting_resource_ids)
        all_ids.extend(bundle.practice_resource_ids)
        all_ids.extend(bundle.reference_resource_ids)

        bundle.all_resource_ids = all_ids[:max_bundle_size]
        bundle.selection_rationales = rationales

        return bundle
