"""
Educational Resource Classifier.
Categorizes discovered web URLs and candidates into canonical ResourceType tiers.
"""

from __future__ import annotations

from urllib.parse import urlparse
from tarkyaan.models.enums import ResourceType


class ResourceClassifier:
    """
    Classifies educational URLs and metadata into canonical ResourceType taxonomy.
    """

    OFFICIAL_DOC_DOMAINS = {
        "docs.python.org", "en.cppreference.com", "cppreference.com",
        "developer.mozilla.org", "docs.oracle.com", "learn.microsoft.com",
        "kubernetes.io", "pytorch.org", "tensorflow.org", "nodejs.org",
        "react.dev", "go.dev", "rust-lang.org"
    }

    PRACTICE_DOMAINS = {
        "leetcode.com", "hackerrank.com", "codeforces.com", "codewars.com",
        "exercism.org", "topcoder.com", "atcoder.jp", "spoj.com"
    }

    ACADEMIC_DOMAINS = {
        "arxiv.org", "ocw.mit.edu", "stanford.edu", "berkeley.edu",
        "ieeexplore.ieee.org", "dl.acm.org", "openreview.net"
    }

    VIDEO_DOMAINS = {
        "youtube.com", "youtu.be", "vimeo.com", "coursera.org", "edx.org"
    }

    @classmethod
    def classify(cls, url: str, title: str = "", snippet: str = "") -> ResourceType:
        """Determine ResourceType from URL domain, path, and text signals."""
        domain = urlparse(url).netloc.lower()
        path = urlparse(url).path.lower()
        text = f"{title} {snippet}".lower()

        # 1. Official Documentation
        if any(d in domain for d in cls.OFFICIAL_DOC_DOMAINS) or "docs" in domain or "/docs/" in path:
            return ResourceType.OFFICIAL_DOCS

        # 2. Practice & Coding Problems
        if any(d in domain for d in cls.PRACTICE_DOMAINS) or "problems" in path or "practice" in path:
            return ResourceType.CODING_PROBLEM

        # 3. Academic / Research Papers
        if any(d in domain for d in cls.ACADEMIC_DOMAINS) or "paper" in text or ".pdf" in path:
            return ResourceType.RESEARCH_PAPER

        # 4. Video & Interactive Courses
        if any(d in domain for d in cls.VIDEO_DOMAINS) or "video" in text or "lecture" in text:
            return ResourceType.VIDEO

        # 5. Interactive Visualizers & Tutorials
        if "visualgo.net" in domain or "interactive" in text or "visualize" in text:
            return ResourceType.INTERACTIVE

        if "tutorial" in text or "tutorial" in path or "guide" in text:
            return ResourceType.TUTORIAL

        if "reference" in text or "cheatsheet" in text or "summary" in text:
            return ResourceType.REFERENCE

        # Default fallback
        return ResourceType.ARTICLE
