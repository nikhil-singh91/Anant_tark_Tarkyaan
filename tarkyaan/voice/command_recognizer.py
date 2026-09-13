"""
Local Voice Command Recognizer for Tarkyaan Phase 5.
Provides deterministic, zero-latency intent recognition for companion controls,
interruption, cancellation, and pedagogical adjustments.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple
from tarkyaan.models.enums import VoiceIntent


class VoiceCommandRecognizer:
    """
    Classifies spoken learner utterances into companion control intents
    without requiring an expensive or slow LLM round-trip.
    """

    INTENT_KEYWORDS: Dict[VoiceIntent, List[str]] = {
        VoiceIntent.INTERRUPT: [
            "stop", "wait", "hold on", "cancel", "never mind", "nevermind",
            "that's enough", "thats enough", "shut up", "quiet", "रुको", "रुकिए",
            "बस", "बस करो", "रहने दो", "शांत रहो"
        ],
        VoiceIntent.PAUSE: [
            "pause", "pause session", "take a break", "रोक दो", "रुकना"
        ],
        VoiceIntent.RESUME: [
            "resume", "continue", "keep going", "go on", "आगे बढ़ो", "जारी रखो", "शुरू करो"
        ],
        VoiceIntent.GIVE_HINT: [
            "give me a hint", "hint", "need a hint", "give hint", "i'm stuck",
            "stuck", "संकेत दो", "मदद करो", "हिंट दो"
        ],
        VoiceIntent.SHOW_ANSWER: [
            "show me the answer", "show answer", "tell me the answer", "what is the answer",
            "give me the solution", "show solution", "उत्तर बताओ", "समाधान दिखाओ"
        ],
        VoiceIntent.EXPLAIN_SIMPLY: [
            "explain simply", "explain it simply", "make it simple", "simpler",
            "eli5", "in simple terms", "सरल भाषा में समझाओ", "आसान भाषा में बताओ"
        ],
        VoiceIntent.EXPLAIN_DEEPLY: [
            "explain deeply", "deep explanation", "formal explanation", "technical details",
            "under the hood", "गहराई से समझाओ", "विस्तार से बताओ"
        ],
        VoiceIntent.GIVE_ANALOGY: [
            "give me an analogy", "analogy", "give an analogy", "visual analogy",
            "उदाहरण दो", "सादृश्य"
        ],
        VoiceIntent.GIVE_EXAMPLE: [
            "give me an example", "show an example", "another example", "more examples",
            "एक उदाहरण दिखाओ", "उदाहरण"
        ],
        VoiceIntent.MAKE_HARDER: [
            "make it harder", "harder", "increase difficulty", "challenge me",
            "more difficult", "कठिन करो", "मुश्किल करो"
        ],
        VoiceIntent.MAKE_EASIER: [
            "make it easier", "easier", "decrease difficulty", "less difficult",
            "सरल करो", "आसान करो"
        ],
        VoiceIntent.SKIP: [
            "skip this", "skip", "next question", "move on", "छोड़ दो", "अगला प्रश्न"
        ],
        VoiceIntent.ASK_QUESTION: [
            "test me", "quiz me", "give me a question", "practice problem", "ask me a question",
            "प्रश्न पूछो", "परीक्षा लो"
        ],
    }

    WAKE_WORDS = [
        r"^hey\s+tarkyaan\b",
        r"^ok\s+tarkyaan\b",
        r"^okay\s+tarkyaan\b",
        r"^tarkyaan\b",
        r"^हे\s+तर्कयान\b",
        r"^तर्कयान\b",
    ]

    @classmethod
    def clean_text(cls, text: str) -> str:
        """Strip punctuation, normalize spaces, and convert to lower case."""
        cleaned = re.sub(r"[^\w\s\u0900-\u097F]", "", text.lower()).strip()
        return re.sub(r"\s+", " ", cleaned)

    @classmethod
    def strip_wake_word(cls, text: str) -> str:
        """Remove leading wake word if present."""
        cleaned = cls.clean_text(text)
        for pattern in cls.WAKE_WORDS:
            cleaned = re.sub(pattern, "", cleaned).strip()
        return cleaned

    @classmethod
    def recognize_intent(cls, utterance: str) -> Tuple[VoiceIntent, Optional[str]]:
        """
        Identify intent and optional argument from user utterance.
        Returns (VoiceIntent, extracted_payload).
        """
        normalized = cls.strip_wake_word(utterance)
        if not normalized:
            return (VoiceIntent.WAKE, None)

        # 1. Exact or prefix match on intent keywords
        for intent, phrases in cls.INTENT_KEYWORDS.items():
            for phrase in phrases:
                clean_phrase = cls.clean_text(phrase)
                if normalized == clean_phrase:
                    return (intent, None)
                # Word boundary check
                if re.search(r"\b" + re.escape(clean_phrase) + r"\b", normalized):
                    return (intent, None)

        # 2. Check for "teach me {concept}" or "explain {concept}"
        teach_match = re.search(r"^(?:teach\s+me|explain|tell\s+me\s+about)\s+(.+)$", normalized)
        if teach_match:
            concept_arg = teach_match.group(1).strip()
            return (VoiceIntent.TEACH_CONCEPT, concept_arg)

        # 3. Check for capability action e.g. "search for {query}"
        search_match = re.search(r"^(?:search\s+for|look\s+up|find\s+resources\s+for)\s+(.+)$", normalized)
        if search_match:
            query_arg = search_match.group(1).strip()
            return (VoiceIntent.RUN_CAPABILITY, query_arg)

        # Default fallback
        return (VoiceIntent.GENERAL_QUERY, normalized)
