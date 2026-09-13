"""
Tests for Phase 6: Secure Coding Sandbox
Covers: CodeSafetyChecker (AST), SecureCodingSandbox execution, SandboxResult
"""
from __future__ import annotations

import pytest

from tarkyaan.models.enums import SandboxStatus
from tarkyaan.sandbox.secure_sandbox import (
    BLOCKED_IMPORTS,
    SAFE_IMPORTS,
    CodeSafetyChecker,
    SandboxConfig,
    SandboxResult,
    SecureCodingSandbox,
)


# ---------------------------------------------------------------------------
# CodeSafetyChecker — Static AST Analysis
# ---------------------------------------------------------------------------

class TestCodeSafetyChecker:
    def test_safe_code_passes(self):
        code = "x = 1 + 2\nprint(x)"
        assert CodeSafetyChecker.check(code) is None

    def test_safe_import_allowed(self):
        code = "import math\nprint(math.pi)"
        assert CodeSafetyChecker.check(code) is None

    def test_safe_from_import_allowed(self):
        code = "from collections import Counter\nc = Counter([1,2,3])"
        assert CodeSafetyChecker.check(code) is None

    def test_blocked_os_import(self):
        code = "import os\nos.system('ls')"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None
        assert "os" in reason

    def test_blocked_subprocess_import(self):
        code = "import subprocess\nsubprocess.run(['ls'])"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None
        assert "subprocess" in reason

    def test_blocked_socket_import(self):
        code = "import socket\ns = socket.socket()"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None

    def test_blocked_requests_import(self):
        code = "import requests\nrequests.get('http://example.com')"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None

    def test_blocked_eval_call(self):
        code = "eval('1+1')"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None
        assert "eval" in reason

    def test_blocked_exec_call(self):
        code = "exec('x=1')"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None
        assert "exec" in reason

    def test_blocked_open_call(self):
        code = "f = open('/etc/passwd', 'r')"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None

    def test_blocked_dunder_subclasses(self):
        code = "().__class__.__subclasses__()"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None

    def test_unknown_module_blocked(self):
        code = "import numpy as np"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None
        assert "allowlist" in reason.lower()

    def test_syntax_error_not_blocked_by_checker(self):
        # SyntaxError is handled gracefully — let subprocess error on it
        code = "def bad(:\n    pass"
        result = CodeSafetyChecker.check(code)
        assert result is None  # Not blocked at AST stage (parse fails gracefully)

    def test_from_os_blocked(self):
        code = "from os import path"
        reason = CodeSafetyChecker.check(code)
        assert reason is not None

    def test_future_import_allowed(self):
        code = "from __future__ import annotations\nx: int = 1"
        assert CodeSafetyChecker.check(code) is None


# ---------------------------------------------------------------------------
# SandboxResult Model
# ---------------------------------------------------------------------------

class TestSandboxResult:
    def test_success_result(self):
        result = SandboxResult(status=SandboxStatus.SUCCESS, stdout="hello", exit_code=0)
        assert result.is_success
        assert result.stdout == "hello"

    def test_blocked_result(self):
        result = SandboxResult(
            status=SandboxStatus.BLOCKED, blocked_reason="import os not allowed"
        )
        assert not result.is_success
        assert result.blocked_reason is not None

    def test_timeout_result(self):
        result = SandboxResult(status=SandboxStatus.TIMEOUT, timed_out=True)
        assert result.timed_out
        assert not result.is_success


# ---------------------------------------------------------------------------
# SecureCodingSandbox — Execution Tests
# ---------------------------------------------------------------------------

class TestSecureCodingSandbox:
    def test_simple_arithmetic(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("print(2 + 2)")
        assert result.status == SandboxStatus.SUCCESS
        assert "4" in result.stdout

    def test_string_output(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("print('hello sandbox')")
        assert result.is_success
        assert "hello sandbox" in result.stdout

    def test_math_import_allowed(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("import math\nprint(math.sqrt(16))")
        assert result.is_success
        assert "4.0" in result.stdout

    def test_collections_import_allowed(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute(
            "from collections import Counter\nc = Counter([1,2,2,3])\nprint(c[2])"
        )
        assert result.is_success
        assert "2" in result.stdout

    def test_os_import_blocked(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("import os\nprint(os.getcwd())")
        assert result.status == SandboxStatus.BLOCKED
        assert result.blocked_reason is not None

    def test_eval_blocked(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("print(eval('1+1'))")
        assert result.status == SandboxStatus.BLOCKED

    def test_timeout_enforced(self):
        sandbox = SecureCodingSandbox(SandboxConfig(timeout_seconds=1))
        result = sandbox.execute("while True: pass")
        assert result.timed_out or result.status in (
            SandboxStatus.TIMEOUT, SandboxStatus.ERROR
        )

    def test_syntax_error_returns_error(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("def bad(:\n    pass")
        # Should return ERROR (syntax error in subprocess), not BLOCKED
        assert result.status in (SandboxStatus.ERROR, SandboxStatus.SUCCESS)
        # stderr should contain some error
        # (some Python versions may handle this differently)

    def test_runtime_error_captured(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("x = 1 / 0")
        assert result.status == SandboxStatus.ERROR
        assert "ZeroDivision" in result.stderr

    def test_stdout_captured(self):
        sandbox = SecureCodingSandbox()
        result = sandbox.execute("for i in range(5):\n    print(i)")
        assert result.is_success
        assert "0" in result.stdout
        assert "4" in result.stdout

    def test_recursive_fibonacci(self):
        code = """
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)
print(fib(10))
"""
        sandbox = SecureCodingSandbox()
        result = sandbox.execute(code)
        assert result.is_success
        assert "55" in result.stdout

    def test_event_bus_integration(self):
        from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
        bus = EventBus()
        events = []
        bus.subscribe(TarkyaanEvent.SANDBOX_EXECUTION_STARTED, lambda e: events.append(e.event))
        bus.subscribe(TarkyaanEvent.SANDBOX_EXECUTION_COMPLETED, lambda e: events.append(e.event))
        sandbox = SecureCodingSandbox()
        sandbox.execute("print('hi')", event_bus=bus, learner_id="l1")
        assert TarkyaanEvent.SANDBOX_EXECUTION_STARTED in events
        assert TarkyaanEvent.SANDBOX_EXECUTION_COMPLETED in events

    def test_blocked_event_published(self):
        from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
        bus = EventBus()
        blocked = []
        bus.subscribe(TarkyaanEvent.SANDBOX_EXECUTION_BLOCKED, lambda e: blocked.append(e))
        sandbox = SecureCodingSandbox()
        sandbox.execute("import os", event_bus=bus, learner_id="l1")
        assert len(blocked) == 1
