"""
Tarkyaan Teaching & Adaptive Explanation Subsystem (Phase 5).
"""

from tarkyaan.teaching.explanation_engine import ExplanationEngine
from tarkyaan.teaching.misconception_tutor import MisconceptionTutor
from tarkyaan.teaching.prerequisite_tutor import PrerequisiteTutor
from tarkyaan.teaching.socratic_engine import SocraticEngine
from tarkyaan.teaching.teaching_engine import TeachingEngine

__all__ = [
    "ExplanationEngine",
    "MisconceptionTutor",
    "PrerequisiteTutor",
    "SocraticEngine",
    "TeachingEngine",
]
