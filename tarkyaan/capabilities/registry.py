"""
Tarkyaan Capability Registry and Discovery Subsystem.
Defines verified system actions, permission boundaries, status tracking, and explainability.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.safety.permissions import PermissionCategory, permission_manager
from tarkyaan.safety.policies import RiskLevel


class CapabilityCategory(str, Enum):
    """Functional domains of Tarkyaan capabilities."""
    RESEARCH = "research"
    LEARNING = "learning"
    MEMORY = "memory"
    VOICE = "voice"
    BROWSER = "browser"
    MAC_AUTOMATION = "mac_automation"
    TERMINAL = "terminal"
    FILESYSTEM = "filesystem"
    COMPUTER_CONTROL = "computer_control"
    ENVIRONMENT = "environment"


class CapabilityStatus(str, Enum):
    """Operational readiness status of an individual capability."""
    AVAILABLE = "available"                      # Fully implemented and runnable
    PARTIAL = "partial"                          # Core functional, advanced features ongoing
    PLANNED = "planned"                          # Architecture & interfaces defined for subsequent phases
    REQUIRES_PERMISSION = "requires_permission"  # Needs macOS OS permissions (mic, screen, accessibility)
    REQUIRES_API = "requires_api"                # Needs external API key configured in .env
    DISABLED = "disabled"                        # Explicitly switched off in settings
    NOT_IMPLEMENTED = "not_implemented"          # Future capability
    UNSUPPORTED = "unsupported"                  # Not supported on current platform/OS


class CapabilityDefinition(BaseModel):
    """Metadata specification and contract for a single capability."""
    name: str
    category: CapabilityCategory
    description: str
    status: CapabilityStatus = Field(default=CapabilityStatus.PLANNED)
    risk_level: RiskLevel = Field(default=RiskLevel.LOW)
    required_permissions: List[PermissionCategory] = Field(default_factory=list)
    required_api_keys: List[str] = Field(default_factory=list)
    requires_confirmation: bool = Field(default=False)
    subsystem: str = Field(default="core")
    execution_timeout_seconds: int = Field(default=30)
    handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True)
    verifier: Optional[Callable[..., bool]] = Field(default=None, exclude=True)


class CapabilityRegistry:
    """
    Central catalog of all verified operations Tarkyaan can perform.
    Enables internal reasoning and honest answering of "What can you do?".
    """

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityDefinition] = {}
        self._register_default_capabilities()

    def register(self, cap: CapabilityDefinition) -> None:
        """Register a verified capability definition."""
        self._capabilities[cap.name] = cap

    def get(self, name: str) -> Optional[CapabilityDefinition]:
        """Retrieve capability definition by name or suffix."""
        if name in self._capabilities:
            return self._capabilities[name]
        for k, v in self._capabilities.items():
            if k.endswith(f".{name}"):
                return v
        return None

    def has(self, name: str) -> bool:
        """Check if capability exists."""
        return self.get(name) is not None

    def list_capabilities(self) -> List[CapabilityDefinition]:
        """Return all registered capabilities."""
        return list(self._capabilities.values())

    list_all = list_capabilities


    def list_available(self) -> List[CapabilityDefinition]:
        """Return all capabilities that are currently executable."""
        available = []
        for cap in self._capabilities.values():
            if cap.status in (CapabilityStatus.AVAILABLE, CapabilityStatus.PARTIAL):
                # Verify permissions
                perm_ok = all(permission_manager.is_granted(p) for p in cap.required_permissions)
                if perm_ok:
                    available.append(cap)
        return available

    def list_by_category(self, category: CapabilityCategory) -> List[CapabilityDefinition]:
        """Return capabilities under a specific category."""
        return [c for c in self._capabilities.values() if c.category == category]

    def is_available(self, name: str) -> bool:
        """Check if capability exists and is currently available."""
        cap = self.get(name)
        if not cap:
            return False
        if cap.status not in (CapabilityStatus.AVAILABLE, CapabilityStatus.PARTIAL):
            return False
        return all(permission_manager.is_granted(p) for p in cap.required_permissions)

    def explain_capabilities(self) -> Dict[str, Any]:
        """
        Generate honest, factual breakdown of what Tarkyaan can and cannot do.
        Never hallucinates non-existent capabilities.
        """
        breakdown: Dict[str, List[str]] = {
            "available": [],
            "partial": [],
            "planned": [],
            "requires_permission": [],
            "requires_api": [],
        }

        for cap in self._capabilities.values():
            if cap.status == CapabilityStatus.AVAILABLE:
                breakdown["available"].append(f"{cap.name}: {cap.description}")
            elif cap.status == CapabilityStatus.PARTIAL:
                breakdown["partial"].append(f"{cap.name}: {cap.description}")
            elif cap.status == CapabilityStatus.PLANNED:
                breakdown["planned"].append(f"{cap.name}: {cap.description}")
            elif cap.status == CapabilityStatus.REQUIRES_PERMISSION:
                perms = ", ".join(p.value for p in cap.required_permissions)
                breakdown["requires_permission"].append(f"{cap.name} (Needs {perms})")
            elif cap.status == CapabilityStatus.REQUIRES_API:
                apis = ", ".join(cap.required_api_keys)
                breakdown["requires_api"].append(f"{cap.name} (Needs {apis})")

        return breakdown

    def _register_default_capabilities(self) -> None:
        """Register the baseline catalog of Tarkyaan capabilities across all domains."""

        # 1. Research Engine (AVAILABLE)
        self.register(
            CapabilityDefinition(
                name="research.web_search",
                category=CapabilityCategory.RESEARCH,
                description="Query web research providers for educational concepts and tutorials.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                required_permissions=[PermissionCategory.NETWORK],
                subsystem="research",
            )
        )
        self.register(
            CapabilityDefinition(
                name="research.evaluate_resource",
                category=CapabilityCategory.RESEARCH,
                description="Multi-dimensional quality, authority, freshness, and learner-fit evaluation.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                subsystem="research",
            )
        )
        self.register(
            CapabilityDefinition(
                name="research.curate_bundle",
                category=CapabilityCategory.RESEARCH,
                description="Synthesize diverse, non-redundant resource bundles for learning tasks.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                subsystem="research",
            )
        )

        # 2. Learning Intelligence (AVAILABLE)
        self.register(
            CapabilityDefinition(
                name="learning.diagnose_knowledge",
                category=CapabilityCategory.LEARNING,
                description="Conduct Socratic diagnostic sessions to evaluate mastery and uncertainty.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                subsystem="assessment",
            )
        )
        self.register(
            CapabilityDefinition(
                name="learning.detect_misconceptions",
                category=CapabilityCategory.LEARNING,
                description="Detect conceptual, algorithmic, and syntax friction patterns.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                subsystem="knowledge",
            )
        )
        self.register(
            CapabilityDefinition(
                name="learning.plan_curriculum",
                category=CapabilityCategory.LEARNING,
                description="Synthesize prerequisite-aware, mastery-calibrated learning roadmaps.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                subsystem="planning",
            )
        )

        # 3. Memory Subsystem (AVAILABLE)
        self.register(
            CapabilityDefinition(
                name="memory.manage_learner_state",
                category=CapabilityCategory.MEMORY,
                description="Store and retrieve learner profiles, mastery states, goals, and history.",
                status=CapabilityStatus.AVAILABLE,
                risk_level=RiskLevel.LOW,
                required_permissions=[PermissionCategory.FILESYSTEM],
                subsystem="memory",
            )
        )

        # 4. Voice Subsystem (PLANNED / ARCHITECTURE)
        self.register(
            CapabilityDefinition(
                name="voice.listen",
                category=CapabilityCategory.VOICE,
                description="Transcribe microphone speech into structured text using Whisper ASR.",
                status=CapabilityStatus.REQUIRES_PERMISSION,
                risk_level=RiskLevel.LOW,
                required_permissions=[PermissionCategory.MICROPHONE],
                subsystem="voice",
            )
        )
        self.register(
            CapabilityDefinition(
                name="voice.speak",
                category=CapabilityCategory.VOICE,
                description="Synthesize natural vocal responses using neural TTS.",
                status=CapabilityStatus.PLANNED,
                risk_level=RiskLevel.LOW,
                subsystem="voice",
            )
        )

        # 5. Mac Automation & Applications (PLANNED / ARCHITECTURE)
        self.register(
            CapabilityDefinition(
                name="mac.launch_application",
                category=CapabilityCategory.MAC_AUTOMATION,
                description="Launch or focus an authorized macOS application.",
                status=CapabilityStatus.PLANNED,
                risk_level=RiskLevel.MEDIUM,
                required_permissions=[PermissionCategory.AUTOMATION],
                subsystem="mac",
            )
        )
        self.register(
            CapabilityDefinition(
                name="mac.system_control",
                category=CapabilityCategory.MAC_AUTOMATION,
                description="Adjust system settings (volume, brightness, media playback).",
                status=CapabilityStatus.PLANNED,
                risk_level=RiskLevel.MEDIUM,
                subsystem="mac",
            )
        )

        # 6. Terminal Execution (PLANNED / RESTRICTED)
        self.register(
            CapabilityDefinition(
                name="terminal.execute_command",
                category=CapabilityCategory.TERMINAL,
                description="Execute bounded shell commands with confirmation and safety checks.",
                status=CapabilityStatus.PLANNED,
                risk_level=RiskLevel.CRITICAL,
                required_permissions=[PermissionCategory.TERMINAL],
                requires_confirmation=True,
                subsystem="terminal",
            )
        )

        # 7. Browser Automation (PLANNED / ARCHITECTURE)
        self.register(
            CapabilityDefinition(
                name="browser.open_url",
                category=CapabilityCategory.BROWSER,
                description="Open verified learning resources in default browser.",
                status=CapabilityStatus.PLANNED,
                risk_level=RiskLevel.MEDIUM,
                required_permissions=[PermissionCategory.NETWORK],
                subsystem="browser",
            )
        )

        # 8. Computer Control & Vision (PLANNED / ARCHITECTURE)
        self.register(
            CapabilityDefinition(
                name="computer.capture_screen",
                category=CapabilityCategory.COMPUTER_CONTROL,
                description="Capture and analyze on-screen educational context via OCR/Vision.",
                status=CapabilityStatus.REQUIRES_PERMISSION,
                risk_level=RiskLevel.HIGH,
                required_permissions=[PermissionCategory.SCREEN_RECORDING],
                subsystem="computer",
            )
        )

        # 9. Filesystem Operations (AVAILABLE / PARTIAL)
        self.register(
            CapabilityDefinition(
                name="fs.create_study_note",
                category=CapabilityCategory.FILESYSTEM,
                description="Create study notes or learning summary files in the workspace.",
                status=CapabilityStatus.PARTIAL,
                risk_level=RiskLevel.HIGH,
                required_permissions=[PermissionCategory.FILESYSTEM],
                subsystem="filesystem",
            )
        )


# Global capability registry singleton for Tarkyaan
capability_registry = CapabilityRegistry()


def explain_capabilities(registry: Optional[CapabilityRegistry] = None) -> str:
    """Format the capability inventory into an honest, user-facing summary."""
    reg = registry or capability_registry
    data = reg.explain_capabilities()
    lines = ["=== Tarkyaan Capability Inventory ==="]

    lines.append("\n[AVAILABLE]")
    for item in data.get("available", []):
        lines.append(f"  ✓ {item}")

    if data.get("partial"):
        lines.append("\n[PARTIAL]")
        for item in data["partial"]:
            lines.append(f"  ~ {item}")

    if data.get("planned"):
        lines.append("\n[PLANNED / ARCHITECTURE]")
        for item in data["planned"]:
            lines.append(f"  ○ {item}")

    if data.get("requires_permission"):
        lines.append("\n[REQUIRES PERMISSION]")
        for item in data["requires_permission"]:
            lines.append(f"  ! {item}")

    if data.get("requires_api"):
        lines.append("\n[REQUIRES API CONFIGURATION]")
        for item in data["requires_api"]:
            lines.append(f"  $ {item}")

    return "\n".join(lines)

