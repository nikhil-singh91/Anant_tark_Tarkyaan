"""Tests for Tarkyaan Capability Registry and Discovery."""

import pytest
from tarkyaan.capabilities.registry import (
    CapabilityCategory,
    CapabilityDefinition,
    CapabilityRegistry,
    CapabilityStatus,
    capability_registry,
    explain_capabilities,
)
from tarkyaan.safety.permissions import PermissionCategory
from tarkyaan.safety.policies import RiskLevel


def test_capability_registry_defaults():
    """Verify built-in capabilities are registered with correct initial states."""
    reg = capability_registry
    all_caps = reg.list_all()
    assert len(all_caps) >= 8

    web_search = reg.get("web_search")
    assert web_search is not None
    assert web_search.category == CapabilityCategory.RESEARCH
    assert web_search.status == CapabilityStatus.AVAILABLE
    assert PermissionCategory.NETWORK in web_search.required_permissions
    assert web_search.risk_level == RiskLevel.LOW

    mac_control = reg.get("launch_application")
    assert mac_control is not None
    assert mac_control.category == CapabilityCategory.MAC_AUTOMATION
    assert mac_control.status in (CapabilityStatus.PLANNED, CapabilityStatus.REQUIRES_PERMISSION)


def test_register_and_get_custom_capability():
    """Test registering a custom capability into an isolated registry."""
    reg = CapabilityRegistry()
    cap = CapabilityDefinition(
        name="math_solver",
        category=CapabilityCategory.RESEARCH,
        description="Solves symbolic mathematical equations",
        required_permissions=[],
        risk_level=RiskLevel.LOW,
        status=CapabilityStatus.AVAILABLE,
    )
    reg.register(cap)

    retrieved = reg.get("math_solver")
    assert retrieved is not None
    assert retrieved.name == "math_solver"
    assert reg.is_available("math_solver") is True


def test_unavailable_and_unsupported_capability():
    """Verify registry distinguishes between unavailable and unregistered capabilities."""
    reg = CapabilityRegistry()
    cap = CapabilityDefinition(
        name="quantum_teleportation",
        category=CapabilityCategory.ENVIRONMENT,
        description="Experimental transport",
        required_permissions=[],
        risk_level=RiskLevel.CRITICAL,
        status=CapabilityStatus.UNSUPPORTED,
    )
    reg.register(cap)

    assert reg.is_available("quantum_teleportation") is False
    q_cap = reg.get("quantum_teleportation")
    assert q_cap is not None
    assert q_cap.status == CapabilityStatus.UNSUPPORTED
    assert reg.get("non_existent_capability") is None
    assert reg.is_available("non_existent_capability") is False


def test_filter_by_category_and_status():
    """Test filtering capabilities by category and availability status."""
    reg = capability_registry
    available_research = reg.list_by_category(CapabilityCategory.RESEARCH)
    assert any("web_search" in c.name for c in available_research)

    available_only = reg.list_available()
    for c in available_only:
        assert c.status in (CapabilityStatus.AVAILABLE, CapabilityStatus.PARTIAL)


def test_explain_capabilities_factual_reporting():
    """Verify explain_capabilities returns accurate, non-hallucinated explanations."""
    explanation = explain_capabilities(capability_registry)
    assert "Tarkyaan Capability Inventory" in explanation
    assert "web_search" in explanation
    assert "AVAILABLE" in explanation
    assert "PLANNED" in explanation or "PARTIAL" in explanation
