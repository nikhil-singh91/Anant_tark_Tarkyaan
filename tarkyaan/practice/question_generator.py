"""
Practice Question Generator for Tarkyaan Phase 5.
Generates multi-type exercises across Difficulty Levels 1-5 with 5-tier progressive hints.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional
from tarkyaan.models.enums import PracticeQuestionType
from tarkyaan.models.practice import PracticeQuestion


class PracticeQuestionGenerator:
    """
    Pedagogical exercise and question generator.
    Produces questions scaled from Level 1 (basic recall) to Level 5 (transfer/novel).
    Each question includes 5 progressive hints adhering to the anti-answer-dumping rule.
    """

    EXERCISE_BANK: Dict[str, Dict[int, List[Dict[str, Any]]]] = {
        "binary_search": {
            1: [
                {
                    "type": PracticeQuestionType.CONCEPTUAL,
                    "prompt": "What essential prerequisite must a dataset satisfy before binary search can be applied to find an element?",
                    "expected_reasoning": "The elements must be ordered (sorted) so that checking the midpoint allows half the search space to be eliminated.",
                    "evaluation_criteria": ["Mentions sorting", "Mentions ordering or monotonic sequence", "Explains why order is necessary"],
                    "hints": [
                        "Think about what property allows you to discard half the elements.",
                        "If the items were completely random, would checking the middle tell you which half contains the target?",
                        "The data must have a definite sequence from smallest to largest.",
                        "The array or list must be strictly sorted.",
                        "Ensure the array is sorted before running binary search."
                    ],
                    "solution": "The collection must be sorted (monotonic). Without ordering, checking the middle element provides zero information about which half contains the target."
                },
                {
                    "type": PracticeQuestionType.MULTIPLE_CHOICE,
                    "prompt": "What is the worst-case time complexity of binary search on a sorted array of size N?\nA) O(1)\nB) O(log N)\nC) O(N)\nD) O(N log N)",
                    "options": ["A) O(1)", "B) O(log N)", "C) O(N)", "D) O(N log N)"],
                    "expected_reasoning": "Each comparison cuts the search space in half, which corresponds mathematically to the logarithm base 2.",
                    "evaluation_criteria": ["Selects B or O(log N)", "Understands halving property"],
                    "hints": [
                        "Consider what happens to the number of elements at each step: N -> N/2 -> N/4...",
                        "How many times can you divide N by 2 until you reach 1?",
                        "The mathematical function that is the inverse of 2^k is log2.",
                        "The time complexity is logarithmic: O(log N).",
                        "Option B: O(log N)."
                    ],
                    "solution": "B) O(log N). Each step cuts the search space in half, taking at most log2(N) comparisons."
                }
            ],
            2: [
                {
                    "type": PracticeQuestionType.APPLICATION,
                    "prompt": "Given the sorted array `arr = [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]` and target `23`:\nIn the first step, what are the values of `low`, `high`, `mid`, and `arr[mid]`?",
                    "expected_reasoning": "low = 0, high = 9, mid = (0 + 9) // 2 = 4, arr[4] = 16",
                    "evaluation_criteria": ["low 0", "high 9", "mid 4", "16"],
                    "hints": [
                        "What is the starting index (low) and ending index (high) of an array of 10 elements?",
                        "Using 0-based indexing: low = 0, high = len(arr) - 1.",
                        "Calculate mid = (0 + 9) // 2.",
                        "mid is index 4. What value is at index 4 in [2, 5, 8, 12, 16, 23, 38, 56, 72, 91]?",
                        "low=0, high=9, mid=4, arr[4]=16."
                    ],
                    "solution": "low = 0, high = 9. mid = 4. arr[mid] = arr[4] = 16. Since 16 < 23, the next search window will be low = 5, high = 9."
                }
            ],
            3: [
                {
                    "type": PracticeQuestionType.CODE_TRACE,
                    "prompt": "Trace the binary search execution for `arr = [3, 9, 14, 19, 25, 31, 42]` and target `14`.\nList the (low, high, mid, arr[mid]) values for each step until target is found.",
                    "expected_reasoning": "Step 1: low=0, high=6, mid=3, arr[3]=19. 14 < 19 -> high=2. Step 2: low=0, high=2, mid=1, arr[1]=9. 14 > 9 -> low=2. Step 3: low=2, high=2, mid=2, arr[2]=14. Found at index 2.",
                    "evaluation_criteria": ["Correct trace of step 1", "Correct pointer update high=2", "Correct step 2 and 3"],
                    "hints": [
                        "Calculate the initial bounds: low=0, high=6. What is mid?",
                        "Step 1: mid = 3, arr[3] = 19. Is 14 smaller or larger than 19?",
                        "Since 14 < 19, update high = mid - 1 = 2.",
                        "Step 2: low=0, high=2. mid = 1, arr[1] = 9. 14 > 9, so low = mid + 1 = 2.",
                        "Step 3: low=2, high=2, mid=2, arr[2]=14 matches target!"
                    ],
                    "solution": "Step 1: (0, 6, 3, 19) -> 14 < 19, high = 2\nStep 2: (0, 2, 1, 9) -> 14 > 9, low = 2\nStep 3: (2, 2, 2, 14) -> match found at index 2."
                }
            ],
            4: [
                {
                    "type": PracticeQuestionType.DEBUGGING,
                    "prompt": "Find the bug in this binary search implementation:\n```python\ndef search(nums, target):\n    low, high = 0, len(nums) - 1\n    while low < high:\n        mid = (low + high) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            low = mid\n        else:\n            high = mid - 1\n    return -1\n```\nWhat happens when target is at index 0 in a single-element array, or when `nums = [2, 5]` and target is 5?",
                    "expected_reasoning": "Two bugs: 1) `while low < high` misses checking when low == high (e.g. single-element array). 2) `low = mid` causes infinite loop when low + 1 == high because mid = low.",
                    "evaluation_criteria": ["Identifies while condition low <= high", "Identifies low = mid + 1 pointer bug", "Explains infinite loop"],
                    "hints": [
                        "Look closely at the while loop termination condition and the update when nums[mid] < target.",
                        "What happens if nums = [7] and target = 7? Does the while loop ever run?",
                        "Notice `while low < high`: if low == high, the loop terminates without checking the last element.",
                        "Also notice `low = mid`: if low=0, high=1, mid=0. If nums[0] < target, low stays 0 forever!",
                        "Fix: Change to `while low <= high:` and `low = mid + 1`."
                    ],
                    "solution": "1) `while low < high` fails on single-element arrays and last-element targets (should be `while low <= high`). 2) `low = mid` creates an infinite loop because mid is integer-divided toward low (should be `low = mid + 1`)."
                }
            ],
            5: [
                {
                    "type": PracticeQuestionType.TRANSFER,
                    "prompt": "You are given an API `isBadVersion(version: int) -> bool` which returns whether a software build is broken. If build k is broken, all subsequent builds k+1, k+2... are also broken.\nGiven N builds [1, 2, ..., N], describe how to find the first bad build in O(log N) calls.",
                    "expected_reasoning": "Binary search on the monotonic answer space [1..N]. low=1, high=N, ans=N. mid = low + (high - low)//2. If isBadVersion(mid) is True, ans=mid, high=mid-1 (search earlier). If False, low=mid+1 (search later).",
                    "evaluation_criteria": ["Recognizes binary search on answer space", "Sets up monotonic predicate", "Correct O(log N) boundary update"],
                    "hints": [
                        "Notice the monotonicity: builds are [Good, Good, ..., Good, Bad, Bad, ..., Bad].",
                        "Can you treat `isBadVersion` as a monotonic predicate P(x) in {0, 1}?",
                        "Maintain low=1, high=N. Check mid.",
                        "If isBadVersion(mid) is True, mid might be the first bad version, or it might be earlier: search left with high = mid - 1.",
                        "If False, mid is good, so first bad version must be strictly to the right: low = mid + 1."
                    ],
                    "solution": "Initialize low=1, high=N, first_bad=N. While low <= high: mid = low + (high - low) // 2. If isBadVersion(mid) is True, record first_bad = mid and search left (high = mid - 1). Else search right (low = mid + 1). Returns first_bad in O(log N)."
                }
            ]
        },
        "recursion": {
            1: [
                {
                    "type": PracticeQuestionType.CONCEPTUAL,
                    "prompt": "What are the two essential components that every correct recursive function must contain?",
                    "expected_reasoning": "1) Base case (stopping condition) and 2) Recursive step (calling itself on a strictly smaller subproblem).",
                    "evaluation_criteria": ["Base case / stopping condition", "Recursive step / smaller subproblem"],
                    "hints": [
                        "Think about what tells the function to stop, and what tells it to keep going.",
                        "One rule prevents infinite loops; the other does the actual problem division.",
                        "The stopping condition is called the base case.",
                        "The self-call on a smaller input is called the recursive case.",
                        "1. Base case, 2. Recursive case."
                    ],
                    "solution": "1. Base Case (stopping condition that returns without further recursion), 2. Recursive Step (calling the function on a strictly smaller subproblem)."
                }
            ],
            2: [
                {
                    "type": PracticeQuestionType.APPLICATION,
                    "prompt": "Write a recursive Python function `sum_to_n(n: int) -> int` that computes the sum of positive integers from 1 up to n (e.g. sum_to_n(3) = 6).",
                    "expected_reasoning": "def sum_to_n(n):\n    if n <= 1:\n        return max(0, n)\n    return n + sum_to_n(n - 1)",
                    "evaluation_criteria": ["n 1", "sum_to_n n 1"],
                    "hints": [
                        "What is the simplest possible input (base case) where you know the answer immediately?",
                        "If n <= 1, return n.",
                        "For any larger n, the sum of 1..n is equal to n plus the sum of 1..(n-1).",
                        "Express that mathematically in code: return n + sum_to_n(n - 1).",
                        "```python\ndef sum_to_n(n):\n    if n <= 1:\n        return n\n    return n + sum_to_n(n - 1)\n```"
                    ],
                    "solution": "```python\ndef sum_to_n(n: int) -> int:\n    if n <= 1:\n        return max(0, n)\n    return n + sum_to_n(n - 1)\n```"
                }
            ],
            3: [
                {
                    "type": PracticeQuestionType.CODE_TRACE,
                    "prompt": "Trace the call stack frames for `factorial(3)` defined as:\n```python\ndef factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n```\nShow the order in which frames are pushed and the order in which they return.",
                    "expected_reasoning": "Push factorial(3) -> Push factorial(2) -> Push factorial(1). factorial(1) returns 1. factorial(2) returns 2 * 1 = 2. factorial(3) returns 3 * 2 = 6.",
                    "evaluation_criteria": ["Shows push order 3, 2, 1", "Shows base case hit at 1", "Shows return unwinding order 1, 2, 6"],
                    "hints": [
                        "Which function call is made first, second, and third?",
                        "Calls are pushed: factorial(3) calls factorial(2), which calls factorial(1).",
                        "Now at factorial(1), base case returns 1.",
                        "Frames unwind in LIFO order: factorial(2) gets 1, returns 2 * 1 = 2.",
                        "Finally factorial(3) gets 2, returns 3 * 2 = 6."
                    ],
                    "solution": "Pushed: factorial(3) -> factorial(2) -> factorial(1).\nUnwound: factorial(1) returns 1 -> factorial(2) returns 2*1=2 -> factorial(3) returns 3*2=6."
                }
            ],
            4: [
                {
                    "type": PracticeQuestionType.DEBUGGING,
                    "prompt": "Why does this function raise `RecursionError` when called with `is_even(5)`?\n```python\ndef is_even(n):\n    if n == 0:\n        return True\n    return is_even(n - 2)\n```\nHow should it be fixed?",
                    "expected_reasoning": "For odd numbers, subtracting 2 skips 0 (5 -> 3 -> 1 -> -1 -> -3...), missing the base case and recursing infinitely. Fix by adding base case `if n < 0: return is_even(-n)` or `if n == 1: return False`.",
                    "evaluation_criteria": ["Explains odd numbers skip 0 to negative numbers", "Provides valid fix (e.g. n == 1 or n < 0)"],
                    "hints": [
                        "Trace the sequence of n values for is_even(5): 5 -> 3 -> 1 -> ?",
                        "What is 1 - 2? Does it ever equal 0?",
                        "Notice n becomes negative: -1, -3, -5... It skips 0 completely!",
                        "The base case only checks `n == 0`. It needs a base case for odd numbers too.",
                        "Fix: Add `if n == 1: return False` or check `if n < 0: return is_even(-n)`."
                    ],
                    "solution": "For odd numbers, n skips past 0 to negative infinity (-1, -3, -5...), so the base case `n == 0` is never satisfied. Fix: Add base case `if n == 1: return False` (or `if n <= 0: return n == 0`)."
                }
            ],
            5: [
                {
                    "type": PracticeQuestionType.TRANSFER,
                    "prompt": "Given a binary tree where each node has `val`, `left`, and `right`:\nWrite a recursive function `max_depth(root)` that returns the maximum depth (height) of the tree. A single node tree has depth 1, empty tree has depth 0.",
                    "expected_reasoning": "def max_depth(root):\n    if not root:\n        return 0\n    return 1 + max(max_depth(root.left), max_depth(root.right))",
                    "evaluation_criteria": ["Base case if not root return 0", "Recursive 1 + max(left, right)"],
                    "hints": [
                        "What is the depth of an empty tree (root is None)?",
                        "If root is None, return 0.",
                        "If root exists, the maximum depth is 1 (for the root itself) plus the maximum depth of its subtrees.",
                        "Recursively compute depth of left and right: max_depth(root.left) and max_depth(root.right).",
                        "Combine them: `return 1 + max(max_depth(root.left), max_depth(root.right))`."
                    ],
                    "solution": "```python\ndef max_depth(root):\n    if not root:\n        return 0\n    return 1 + max(max_depth(root.left), max_depth(root.right))\n```"
                }
            ]
        }
    }

    @classmethod
    def generate_question(
        cls,
        concept_id: str,
        concept_name: Optional[str] = None,
        difficulty: int = 2,
        question_type: Optional[PracticeQuestionType] = None,
        session_id: Optional[str] = None,
        learner_id: str = ""
    ) -> PracticeQuestion:
        """Generate a practice question matched to concept and target difficulty."""
        diff = max(1, min(5, difficulty))
        c_key = concept_id.lower().replace(" ", "_")

        matched_bank = None
        for k in cls.EXERCISE_BANK:
            if k in c_key or c_key in k:
                matched_bank = cls.EXERCISE_BANK[k]
                break

        if matched_bank and diff in matched_bank:
            candidates = matched_bank[diff]
            selected = candidates[0]
            if question_type:
                for cand in candidates:
                    if cand.get("type") == question_type:
                        selected = cand
                        break
            return PracticeQuestion(
                learner_id=learner_id,
                session_id=session_id,
                concept_id=concept_id,
                concept_name=concept_name or concept_id.replace("_", " ").title(),
                question_type=selected.get("type", PracticeQuestionType.CONCEPTUAL),
                difficulty=diff,
                prompt=selected["prompt"],
                options=selected.get("options", []),
                expected_reasoning=selected["expected_reasoning"],
                evaluation_criteria=selected["evaluation_criteria"],
                hints=selected["hints"],
                solution_explanation=selected["solution"]
            )

        # Fallback dynamic exercise
        c_disp = concept_name or concept_id.replace("_", " ").title()
        return PracticeQuestion(
            learner_id=learner_id,
            session_id=session_id,
            concept_id=concept_id,
            concept_name=c_disp,
            question_type=question_type or PracticeQuestionType.CONCEPTUAL,
            difficulty=diff,
            prompt=f"Explain the primary operational invariant of {c_disp} and how it prevents errors at runtime.",
            expected_reasoning=f"Must identify valid state preconditions and describe error prevention in {c_disp}.",
            evaluation_criteria=["Mentions preconditions", "Mentions state invariants", "Describes error prevention"],
            hints=[
                f"Consider what condition must always be true for {c_disp}.",
                f"Think about the input data structure required by {c_disp}.",
                f"Recall how {c_disp} handles boundary conditions.",
                f"Focus on the step where {c_disp} validates invariants.",
                f"In {c_disp}, state validation guarantees algorithmic correctness."
            ],
            solution_explanation=f"{c_disp} relies on strict state preconditions to ensure reliable algorithmic execution."
        )
