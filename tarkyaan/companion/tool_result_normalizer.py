"""
Tool Result Normalizer.
Translates raw tool outputs and capability execution states into pedagogical summaries
suitable for voice TTS and conversational learning feedback.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from tarkyaan.agent.observability import AgentObservabilityRecorder


class ToolResultNormalizer:
    """
    Formats raw tool responses into concise, student-friendly pedagogical language.
    Masks credentials and technical noise.
    """

    @classmethod
    def normalize_result(cls, capability_id: str, raw_output: Dict[str, Any]) -> str:
        """Produce a clean, natural-language explanation of what a capability did."""
        cap = capability_id.lower()

        # 1. Application Actions
        if "app" in cap:
            app_name = raw_output.get("app_name", "Application")
            verified = raw_output.get("verified", False)
            if verified:
                return f"I opened {app_name} and verified it is ready for your study session."
            return f"I attempted to launch {app_name}, but it is not currently responsive."

        # 2. Filesystem Actions
        if "fs" in cap or "filesystem" in cap:
            if "structure" in raw_output:
                struct = raw_output["structure"]
                name = getattr(struct, "project_name", "project")
                files_count = getattr(struct, "total_files", 0)
                lang = getattr(struct, "primary_language", "code")
                return f"I explored the {name} project structure. It contains {files_count} {lang} files."
            if "content" in raw_output:
                return "I inspected the requested file and analyzed the code structure."
            return "Filesystem operation completed."

        # 3. Browser Actions
        if "browser" in cap:
            title = raw_output.get("extracted_title", "web page")
            if raw_output.get("prompt_injection_detected"):
                return f"I inspected {title}, but ignored untrusted instruction overrides on the page."
            return f"I found educational resources from {title}."

        # 4. Terminal Actions
        if "terminal" in cap:
            if raw_output.get("blocked_by_safety"):
                return "That terminal command was blocked by safety policy because it contains destructive flags."
            if raw_output.get("requires_confirmation"):
                return "This command requires your explicit confirmation before it can run."
            exit_code = raw_output.get("exit_code", 0)
            if exit_code == 0:
                return "The command finished successfully with zero errors."
            return f"The command completed with exit code {exit_code}."

        # 5. Sandbox Execution
        if "sandbox" in cap:
            success = raw_output.get("success", False)
            if success:
                return "Your code ran cleanly in the secure sandbox with passing tests."
            err = raw_output.get("error", "runtime error")
            return f"The code encountered an issue in the sandbox: {err}"

        # Default fallback
        summary = str(raw_output.get("summary", "Action completed successfully."))
        return AgentObservabilityRecorder.redact_secrets(summary)
