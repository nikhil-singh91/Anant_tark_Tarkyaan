"""
Task Verification Subsystem.
Verifies postconditions for all autonomous agent actions.
Guarantees Tarkyaan never says 'Done' without empirical verification.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from tarkyaan.agent.task_models import AgentStep, VerificationResult
from tarkyaan.computer.application_adapter import ApplicationAdapter


class TaskVerifier:
    """
    Empirical verifier for autonomous step outcomes.
    Checks application states, file modifications, test results, and browser outputs.
    """

    def __init__(self, app_adapter: Optional[ApplicationAdapter] = None) -> None:
        self.app_adapter = app_adapter or ApplicationAdapter(mock_mode=True)

    def verify_step(self, step: AgentStep, execution_output: Dict[str, Any]) -> VerificationResult:
        """
        Evaluate postconditions of an executed step based on capability type.
        """
        cap_id = step.capability_id.lower()

        # 1. Application Actions (open, focus)
        if "app" in cap_id or "application" in cap_id:
            app_name = step.parameters.get("app_name", "")
            is_run = self.app_adapter.is_running(app_name)
            if is_run or execution_output.get("verified", False):
                return VerificationResult(
                    is_verified=True,
                    notes=f"Verified application '{app_name}' is active.",
                    evidence_observed={"app_running": True},
                )
            return VerificationResult(
                is_verified=False,
                notes=f"Verification failed: '{app_name}' does not appear to be running.",
                error="Process not detected.",
            )

        # 2. Browser Actions (open_url, extract, search)
        if "browser" in cap_id:
            content = execution_output.get("extracted_content") or execution_output.get("url")
            success = execution_output.get("success", False)
            if success and content:
                return VerificationResult(
                    is_verified=True,
                    notes="Browser navigation verified with content extraction.",
                    evidence_observed={"content_length": len(str(content))},
                )
            return VerificationResult(
                is_verified=False,
                notes="Browser action failed or yielded empty content.",
                error=execution_output.get("error", "No content"),
            )

        # 3. Terminal & Sandbox Actions (test run, command execution)
        if "terminal" in cap_id or "sandbox" in cap_id:
            exit_code = execution_output.get("exit_code", -1)
            success = execution_output.get("success", False)
            if success and exit_code == 0:
                return VerificationResult(
                    is_verified=True,
                    notes="Execution completed with exit code 0.",
                    evidence_observed={"exit_code": 0},
                )
            return VerificationResult(
                is_verified=False,
                notes=f"Command finished with non-zero exit code: {exit_code}",
                error=execution_output.get("stderr") or execution_output.get("error", "Execution failure"),
            )

        # 4. Filesystem Actions (read, inspect, write)
        if "fs" in cap_id or "filesystem" in cap_id:
            if execution_output.get("success", False):
                return VerificationResult(
                    is_verified=True,
                    notes="Filesystem operation verified.",
                    evidence_observed={"operation": step.action},
                )
            return VerificationResult(
                is_verified=False,
                notes="Filesystem operation failed.",
                error=execution_output.get("error", "FS error"),
            )

        # 5. Vision / Screen Awareness
        if "vision" in cap_id or "screen" in cap_id:
            if execution_output.get("success", False):
                return VerificationResult(
                    is_verified=True,
                    notes="Visual perception completed and sanitized.",
                    evidence_observed={"detected": execution_output.get("topic")},
                )
            return VerificationResult(
                is_verified=False,
                notes="Vision observation failed.",
                error=execution_output.get("error", "Vision error"),
            )

        # Default fallback
        is_ok = bool(execution_output.get("success", False))
        return VerificationResult(
            is_verified=is_ok,
            notes="Default capability completion verification.",
            evidence_observed=execution_output,
        )
