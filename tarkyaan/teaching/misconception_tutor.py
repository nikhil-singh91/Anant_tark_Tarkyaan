"""
Misconception Tutor for Tarkyaan Phase 5.
Detects and resolves cognitive friction points using mental model contrast,
counterexamples, and verified re-checking.
"""

from __future__ import annotations

from typing import Dict, List, Optional
from tarkyaan.models.teaching import MisconceptionIntervention


class MisconceptionTutor:
    """
    Pedagogical misconception remediation engine.
    Instead of simply saying 'that is incorrect', this engine:
    1. Identifies the specific misconception.
    2. Explains why it is intuitive or tempting.
    3. Contrasts flawed vs correct mental models side-by-side.
    4. Delivers a concrete counterexample demonstrating failure.
    5. Asks the learner to re-evaluate with the valid model.
    """

    MISCONCEPTION_CATALOG: Dict[str, Dict[str, str]] = {
        "binary_search_unsorted": {
            "description": "Believing binary search works on any arbitrary unsorted array.",
            "why_tempting": "Because binary search looks at elements by index, it is easy to assume checking the middle works regardless of how elements are arranged.",
            "flawed_mental_model": "Checking the midpoint lets us discard half the array no matter what numbers are where.",
            "correct_mental_model": "Discarding half the array is ONLY valid when the array is sorted. If it is unsorted, the target might be in the discarded half!",
            "counterexample": "Look for 9 in unsorted array [5, 9, 2, 1, 8]. Midpoint is index 2 (value 2). Since 9 > 2, binary search would throw away the left half [5, 9], permanently losing the target 9!",
            "corrective_check_question": "If you are given an unsorted array of numbers, what mandatory step must you perform before you can safely run binary search?",
            "expected_reasoning": "You must sort the array first (e.g. O(n log n)), or use linear search (O(n))."
        },
        "binary_search_off_by_one": {
            "description": "Setting `low = mid` instead of `low = mid + 1`, causing infinite loops.",
            "why_tempting": "It feels safer not to skip past `mid` in case we miss something.",
            "flawed_mental_model": "`mid` might be adjacent to the answer, so keep it in the window.",
            "correct_mental_model": "We already checked `arr[mid]` and confirmed it is strictly less than target. Mid cannot be the answer. If `low = 0, high = 1`, `mid = 0`. Setting `low = mid` changes nothing, looping forever.",
            "counterexample": "Search for 5 in [3, 5] (low=0, high=1). mid = 0 (val 3). 3 < 5. If you set low = mid (low=0), the window remains [0, 1] forever.",
            "corrective_check_question": "Why is it completely safe to advance `low = mid + 1` when `arr[mid] < target`?",
            "expected_reasoning": "Because arr[mid] was already tested and is not the target, so it can be eliminated."
        },
        "recursion_no_base_case": {
            "description": "Assuming recursive calls naturally stop when numbers get small or empty.",
            "why_tempting": "In human thinking, tasks naturally finish when nothing is left, so beginners assume computers know when to stop.",
            "flawed_mental_model": "The function will stop calling itself once the numbers reach zero or the end.",
            "correct_mental_model": "A computer blindly executes function instructions. Without an explicit base case check, it continues decrementing into negative numbers forever until call stack memory is exhausted.",
            "counterexample": "def count(n): count(n - 1). Calling count(1) calls count(0), count(-1), count(-2)... until RecursionError crashes the program.",
            "corrective_check_question": "What happens in memory when a recursive function lacks a base case?",
            "expected_reasoning": "Stack frames keep getting allocated on the call stack until memory is exhausted, causing a stack overflow."
        },
        "recursion_return_missing": {
            "description": "Calling a recursive function without returning its result (`func(n-1)` instead of `return func(n-1)`).",
            "why_tempting": "It feels like calling the function already does the computation, forgetting the value must be passed back up the call stack.",
            "flawed_mental_model": "The recursive call computes the result in the background so the parent function has it automatically.",
            "correct_mental_model": "Each function call has its own isolated stack frame. If you do not explicitly return the result of the child call, the parent returns `None`.",
            "counterexample": "In `def fact(n): if n<=1: return 1; fact(n-1)*n`. For fact(3), the top frame returns None because fact(2) didn't return its multiplication!",
            "corrective_check_question": "Why does a recursive function return None if you omit the `return` keyword before the recursive call in Python?",
            "expected_reasoning": "Because in Python, functions that execute without an explicit return statement default to returning None."
        }
    }

    def generate_intervention(
        self,
        concept_id: str,
        misconception_key_or_desc: str
    ) -> MisconceptionIntervention:
        """Create a targeted 5-step cognitive intervention."""
        key = misconception_key_or_desc.lower()
        matched = None

        for k, entry in self.MISCONCEPTION_CATALOG.items():
            if k in key or any(word in key for word in k.split("_")):
                matched = (k, entry)
                break

        if not matched:
            # Check concept name
            if "binary" in concept_id.lower() or "search" in concept_id.lower():
                matched = ("binary_search_unsorted", self.MISCONCEPTION_CATALOG["binary_search_unsorted"])
            elif "recurs" in concept_id.lower():
                matched = ("recursion_no_base_case", self.MISCONCEPTION_CATALOG["recursion_no_base_case"])
            else:
                matched = (
                    "general_misconception",
                    {
                        "description": f"Misunderstanding core operational assumptions of {concept_id}.",
                        "why_tempting": "It is intuitive to apply simplified heuristics without validating invariants.",
                        "flawed_mental_model": "Assuming operations succeed without prerequisite validation.",
                        "correct_mental_model": "Preconditions must be strictly verified before applying the algorithm.",
                        "counterexample": f"Applying {concept_id} with invalid boundary conditions causes silent failures or incorrect results.",
                        "corrective_check_question": f"What invariant must always be checked before applying {concept_id}?",
                        "expected_reasoning": "Verifying inputs and constraints."
                    }
                )

        k_id, data = matched
        return MisconceptionIntervention(
            misconception_id=k_id,
            concept_id=concept_id,
            misconception_description=data["description"],
            why_tempting=data["why_tempting"],
            flawed_mental_model=data["flawed_mental_model"],
            correct_mental_model=data["correct_mental_model"],
            counterexample=data["counterexample"],
            corrective_check_question=data["corrective_check_question"],
            expected_reasoning=data["expected_reasoning"]
        )
