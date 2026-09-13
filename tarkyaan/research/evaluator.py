"""
Multi-Dimensional Resource Quality and Learner-Fit Evaluator.
Computes quantified, transparent sub-scores across 8 pedagogical dimensions.
"""

from __future__ import annotations

from typing import List, Optional, Tuple
from urllib.parse import urlparse

from tarkyaan.models.enums import ResourceType, SourceAuthorityTier, TaskType
from tarkyaan.models.learner import LearnerProfile
from tarkyaan.models.research import ResearchIntent, ResourceDimensionScores, SearchResultCandidate


class ResourceEvaluator:
    """
    Evaluates discovered candidate resources across 8 transparent pedagogical dimensions.
    """

    OFFICIAL_DOMAINS = {
        "docs.python.org", "en.cppreference.com", "cppreference.com",
        "developer.mozilla.org", "docs.oracle.com", "learn.microsoft.com",
        "kubernetes.io", "pytorch.org", "tensorflow.org", "go.dev", "rust-lang.org"
    }

    INSTITUTIONAL_DOMAINS = {
        "ocw.mit.edu", "stanford.edu", "berkeley.edu", "harvard.edu",
        "arxiv.org", "ieeexplore.ieee.org", "acm.org"
    }

    REPUTABLE_EDUCATIONAL_DOMAINS = {
        "leetcode.com", "geeksforgeeks.org", "khanacademy.org",
        "visualgo.net", "exercism.org", "freecodecamp.org", "realpython.com"
    }

    @classmethod
    def evaluate(
        cls,
        candidate: SearchResultCandidate,
        intent: ResearchIntent,
        learner: Optional[LearnerProfile] = None,
        task_type: TaskType = TaskType.LEARN,
        resource_type: ResourceType = ResourceType.ARTICLE
    ) -> Tuple[ResourceDimensionScores, List[str]]:
        """
        Compute transparent 8-dimension scores and textual evaluation notes.
        """
        notes: List[str] = []
        domain = candidate.source_domain.lower() or urlparse(candidate.url).netloc.lower()
        text = f"{candidate.title} {candidate.snippet}".lower()
        concept_term = (intent.concept_name or intent.concept_id or "").replace("_", " ").lower()

        # 1. Authority Score
        if any(d in domain for d in cls.OFFICIAL_DOMAINS):
            authority = 0.95
            notes.append(f"High authority: official documentation source ({domain}).")
        elif any(d in domain for d in cls.INSTITUTIONAL_DOMAINS):
            authority = 0.90
            notes.append(f"High authority: peer-reviewed academic or university source ({domain}).")
        elif any(d in domain for d in cls.REPUTABLE_EDUCATIONAL_DOMAINS):
            authority = 0.80
            notes.append(f"Recognized educational platform ({domain}).")
        else:
            authority = 0.55
            notes.append(f"Community / secondary source ({domain}).")

        # 2. Relevance Score
        relevance = 0.4
        if concept_term in candidate.title.lower():
            relevance += 0.35
        elif any(w in candidate.title.lower() for w in concept_term.split()):
            relevance += 0.20

        if concept_term in candidate.snippet.lower():
            relevance += 0.20
        relevance = min(1.0, relevance)

        # 3. Quality Score
        quality = 0.70
        # Penalize thin snippets
        if len(candidate.snippet.strip()) < 40:
            quality -= 0.20
            notes.append("Short/thin snippet preview reduces quality confidence.")
        # Check suspicious keywords
        if any(w in text for w in ("click here", "buy now", "advertisement", "sponsored")):
            quality -= 0.30
            notes.append("Commercial or promotional markers detected.")
        quality = max(0.2, min(1.0, quality))

        # 4. Difficulty Fit
        # Target difficulty: 1 (beginner) to 5 (expert)
        target_diff = intent.difficulty
        is_beginner_resource = any(w in text for w in ("beginner", "basics", "introduction", "101", "intro"))
        is_advanced_resource = any(w in text for w in ("advanced", "internals", "optimization", "proof", "master theorem"))

        if target_diff <= 2:
            diff_fit = 0.90 if is_beginner_resource else (0.50 if is_advanced_resource else 0.75)
        elif target_diff >= 4:
            diff_fit = 0.90 if is_advanced_resource else (0.60 if is_beginner_resource else 0.80)
        else:
            diff_fit = 0.85

        # 5. Learner Fit
        learner_fit = 0.75
        if intent.programming_language:
            lang_term = intent.programming_language.lower()
            if lang_term in text or lang_term in candidate.url.lower():
                learner_fit += 0.20
                notes.append(f"Matches learner language preference ({intent.programming_language}).")
            else:
                learner_fit -= 0.10

        # Task type alignment
        if task_type in (TaskType.PRACTICE, TaskType.SOLVE) and resource_type in (ResourceType.CODING_PROBLEM, ResourceType.EXERCISE):
            learner_fit += 0.15
            notes.append("Strong task-type alignment: hands-on practice problems.")
        elif task_type in (TaskType.LEARN, TaskType.UNDERSTAND) and resource_type in (ResourceType.TUTORIAL, ResourceType.OFFICIAL_DOCS, ResourceType.INTERACTIVE):
            learner_fit += 0.15
            notes.append("Strong task-type alignment: conceptual explanation.")

        learner_fit = max(0.1, min(1.0, learner_fit))

        # 6. Freshness (Domain sensitive)
        # For fundamental algorithms, mathematics, and CS theory, age does not reduce validity
        is_timeless = any(c in concept_term for c in ("algorithm", "binary search", "recursion", "sorting", "math", "graph"))
        freshness = 0.90 if is_timeless else 0.75

        # 7. Practical Usefulness
        has_code = any(k in text for k in ("def ", "code", "example", "function", "int main", "solution"))
        practical = 0.85 if has_code else 0.65

        # 8. Confidence
        confidence = 0.80 if candidate.snippet else 0.50

        # Overall composite calculation
        overall = (
            0.25 * relevance +
            0.20 * learner_fit +
            0.15 * authority +
            0.15 * diff_fit +
            0.10 * quality +
            0.10 * practical +
            0.05 * freshness
        )

        scores = ResourceDimensionScores(
            relevance=round(relevance, 2),
            authority=round(authority, 2),
            quality=round(quality, 2),
            difficulty_fit=round(diff_fit, 2),
            learner_fit=round(learner_fit, 2),
            freshness=round(freshness, 2),
            practical_usefulness=round(practical, 2),
            confidence=round(confidence, 2),
            overall=round(min(1.0, max(0.0, overall)), 2),
        )

        return scores, notes
