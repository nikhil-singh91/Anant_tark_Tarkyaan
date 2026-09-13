"""
Socratic Teaching Engine for Tarkyaan Phase 5.
Generates purposeful, inquiry-based pedagogical probes to stimulate active reasoning
rather than passive absorption.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from tarkyaan.models.teaching import SocraticProbe


class SocraticEngine:
    """
    Socratic inquiry generator.
    Produces questions that challenge assumptions, prompt prediction, and verify invariants.
    """

    PROBE_CATALOG: Dict[str, List[Dict[str, Any]]] = {
        "binary search": [
            {
                "probe_question": "What fundamental property of the array allows us to safely discard an entire half after just one comparison?",
                "pedagogical_intent": "Verify understanding of the monotonic ordering precondition.",
                "target_insight": "The array must be sorted (monotonic) so every element to the left is <= and to the right is >=.",
                "expected_keywords": ["sorted", "order", "monotonic", "less", "greater", "half"],
                "followup_if_correct": "Spot on. Because it's sorted, arr[mid] acts as a dividing partition. What would happen if the array was scrambled?",
                "followup_if_struggling": "Think about what guarantees that all numbers after the midpoint are bigger than the midpoint. What must be true about the array before we start?",
            },
            {
                "probe_question": "If you are searching for an element in an array of size 1024, how many comparisons will binary search make in the absolute worst case?",
                "pedagogical_intent": "Prompt algorithmic complexity deduction from first principles.",
                "target_insight": "10 comparisons, because 1024 = 2^10, and each step halves the remaining candidates.",
                "expected_keywords": ["10", "log", "ten", "halv"],
                "followup_if_correct": "Exactly right: log2(1024) = 10. Just 10 checks for over a thousand elements!",
                "followup_if_struggling": "Remember that each step divides the search space by 2: 1024 -> 512 -> 256... How many times can you divide 1024 by 2 until you reach 1?",
            },
            {
                "probe_question": "When `arr[mid] < target`, why do we advance `low = mid + 1` instead of simply `low = mid`?",
                "pedagogical_intent": "Prevent infinite loop and off-by-one pointer convergence errors.",
                "target_insight": "Since arr[mid] is strictly less than target, mid itself cannot be the target, and including it can cause an infinite loop when low + 1 == high.",
                "expected_keywords": ["infinite loop", "already checked", "not the target", "stuck", "eliminate mid"],
                "followup_if_correct": "Precisely. We already verified mid isn't the target, so we eliminate it and guarantee the search window strictly shrinks.",
                "followup_if_struggling": "Consider what happens if `low = 0` and `high = 1`. If `mid = 0` and you set `low = mid`, did `low` change at all?",
            }
        ],
        "recursion": [
            {
                "probe_question": "What essential component must every recursive function have to prevent it from calling itself forever?",
                "pedagogical_intent": "Emphasize base case termination guarantee.",
                "target_insight": "A base case (termination condition) that returns without making further recursive calls.",
                "expected_keywords": ["base case", "stopping condition", "termination", "exit condition"],
                "followup_if_correct": "Exactly. The base case anchors the recursion and halts the creation of new stack frames.",
                "followup_if_struggling": "Think about how the function knows when it has reached the smallest possible problem and can stop.",
            },
            {
                "probe_question": "Where does the computer store the local variables and pending return address while a recursive call is executing?",
                "pedagogical_intent": "Instill mental model of call stack frames.",
                "target_insight": "On the call stack, where each function invocation receives its own stack frame.",
                "expected_keywords": ["call stack", "stack", "stack frame", "memory"],
                "followup_if_correct": "Exactly right. Each call pushes a stack frame; once the base case returns, they unwind in LIFO order.",
                "followup_if_struggling": "Think about what data structure behaves like a stack of plates where the last plate placed on top is the first one taken off.",
            },
            {
                "probe_question": "If you double the input size n in a naive Fibonacci recursive function, what happens to the total number of function calls?",
                "pedagogical_intent": "Expose exponential branching complexity.",
                "target_insight": "The number of calls explodes exponentially (approximately doubles for each +1 to n, so for 2n it squares).",
                "expected_keywords": ["exponential", "double", "explode", "huge", "tree", "2^n"],
                "followup_if_correct": "Right. Each call splits into two child calls, forming an exponential call tree of O(2^n).",
                "followup_if_struggling": "Draw out fib(4): it calls fib(3) and fib(2). fib(3) calls fib(2) and fib(1)... How many branches grow at each layer?",
            }
        ]
    }

    def generate_probe(
        self,
        concept_id: str,
        concept_name: Optional[str] = None,
        probe_index: int = 0
    ) -> SocraticProbe:
        """Generate a pedagogical inquiry question for the concept."""
        key = (concept_name or concept_id).lower()
        matched_catalog: Optional[List[Dict[str, Any]]] = None

        for catalog_key in self.PROBE_CATALOG:
            if catalog_key in key:
                matched_catalog = self.PROBE_CATALOG[catalog_key]
                break

        if matched_catalog:
            entry = matched_catalog[probe_index % len(matched_catalog)]
            return SocraticProbe(
                concept_id=concept_id,
                probe_question=entry["probe_question"],
                pedagogical_intent=entry["pedagogical_intent"],
                target_insight=entry["target_insight"],
                expected_keywords=entry["expected_keywords"],
                followup_if_correct=entry["followup_if_correct"],
                followup_if_struggling=entry["followup_if_struggling"],
            )

        # Generic fallback Socratic probe
        c_name = concept_name or concept_id
        return SocraticProbe(
            concept_id=concept_id,
            probe_question=f"What core assumption must hold true for {c_name} to produce correct results?",
            pedagogical_intent=f"Stimulate inquiry into precondition invariants of {c_name}.",
            target_insight=f"Valid inputs and proper invariants must be maintained throughout {c_name}.",
            expected_keywords=["invariant", "valid", "precondition", "assumption", "correct"],
            followup_if_correct=f"Excellent insight into the invariants of {c_name}.",
            followup_if_struggling=f"Consider what would break if the input assumptions of {c_name} were violated.",
        )

    def evaluate_probe_response(
        self,
        probe: SocraticProbe,
        learner_response: str
    ) -> Dict[str, Any]:
        """
        Evaluate learner reply against probe's target insight and expected keywords.
        Returns correctness status, feedback response, and pedagogical advice.
        """
        resp_clean = learner_response.lower().strip()
        has_negation = bool(re.search(r"\b(without|no|not|never|don't|dont|doesnt|doesn't)\b", resp_clean))

        keyword_hits = [kw for kw in probe.expected_keywords if re.search(r"\b" + re.escape(kw), resp_clean)]

        # Insight requires positive keyword match without contradicting negation
        has_insight = (len(keyword_hits) >= 1) and not has_negation

        if has_insight:
            return {
                "achieved_insight": True,
                "feedback": probe.followup_if_correct,
                "confidence": 0.85,
                "keyword_hits": keyword_hits,
            }
        else:
            return {
                "achieved_insight": False,
                "feedback": probe.followup_if_struggling,
                "confidence": 0.50,
                "keyword_hits": keyword_hits,
            }
