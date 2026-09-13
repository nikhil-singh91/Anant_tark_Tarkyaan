"""Research engine package for Tarkyaan.

Provides autonomous research, source discovery, web search provider abstraction,
metadata extraction, quality evaluation across 8 dimensions, deterministic ranking,
diverse bundle curation, and prompt injection defense.
"""

from tarkyaan.research.cache import ResearchCache
from tarkyaan.research.classifier import ResourceClassifier
from tarkyaan.research.curator import ResourceCurator
from tarkyaan.research.evaluator import ResourceEvaluator
from tarkyaan.research.extractor import ResourceExtractor
from tarkyaan.research.normalizer import URLNormalizer
from tarkyaan.research.providers.base import SearchOptions, SearchProvider, SearchResponse
from tarkyaan.research.providers.mock import MockSearchProvider
from tarkyaan.research.providers.tavily import TavilySearchProvider
from tarkyaan.research.query_generator import QueryGenerator
from tarkyaan.research.ranker import ResourceRanker
from tarkyaan.research.research_engine import ResearchEngine

__all__ = [
    "ResearchEngine",
    "QueryGenerator",
    "URLNormalizer",
    "ResourceExtractor",
    "ResourceClassifier",
    "ResourceEvaluator",
    "ResourceRanker",
    "ResourceCurator",
    "ResearchCache",
    "SearchProvider",
    "SearchOptions",
    "SearchResponse",
    "MockSearchProvider",
    "TavilySearchProvider",
]
