"""
Tarkyaan Provider Manager.
Central registry for pluggable LLM, search, voice, and tool providers.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from tarkyaan.providers.base import BaseProvider, LLMProvider, ProviderHealth, ProviderType, VoiceSTTProvider, VoiceTTSProvider


class ProviderManager:
    """
    Thread-safe manager for registering and accessing external service providers.
    Enforces clean separation between provider logic and educational algorithms.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._providers: Dict[str, BaseProvider] = {}
        self._default_providers: Dict[ProviderType, str] = {}

    def register(self, provider: BaseProvider, is_default: bool = False) -> None:
        """Register a provider instance and optionally set it as default for its type."""
        with self._lock:
            self._providers[provider.name] = provider
            if is_default or provider.provider_type not in self._default_providers:
                self._default_providers[provider.provider_type] = provider.name

    def get(self, name: str) -> Optional[BaseProvider]:
        """Retrieve a specific provider by name."""
        with self._lock:
            return self._providers.get(name)

    def get_default(self, p_type: ProviderType) -> Optional[BaseProvider]:
        """Retrieve the designated default provider for a category."""
        with self._lock:
            name = self._default_providers.get(p_type)
            return self._providers.get(name) if name else None

    def list_providers(self) -> List[BaseProvider]:
        """Return all registered providers."""
        with self._lock:
            return list(self._providers.values())

    def check_health_all(self) -> Dict[str, ProviderHealth]:
        """Execute health checks across all registered providers."""
        results: Dict[str, ProviderHealth] = {}
        with self._lock:
            providers = list(self._providers.values())

        for p in providers:
            try:
                results[p.name] = p.health_check()
            except Exception as exc:  # noqa: BLE001
                results[p.name] = ProviderHealth(
                    provider_name=p.name,
                    provider_type=p.provider_type,
                    is_available=False,
                    status_message=f"Health check failed: {exc}"
                )
        return results


# Global provider manager singleton
provider_manager = ProviderManager()
