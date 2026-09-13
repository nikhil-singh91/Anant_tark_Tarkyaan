"""Tests for Filesystem Learning Capability and Security Boundaries."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
import pytest

from tarkyaan.filesystem.filesystem_capability import (
    FilesystemActionResult,
    FilesystemCapability,
    ProjectStructure,
)


def test_filesystem_inspect_project_structure():
    """Verify filesystem capability maps project hierarchy and finds entry points."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "main.py").write_text("def run():\n    print('Running')\n", encoding="utf-8")
        (root / "utils.py").write_text("def helper():\n    return 42\n", encoding="utf-8")
        (root / "sub").mkdir()
        (root / "sub" / "algo.py").write_text("def binary_search():\n    pass\n", encoding="utf-8")

        fs = FilesystemCapability(base_dir=str(root))
        res: FilesystemActionResult = fs.inspect_project_structure()

        assert res.success is True
        assert res.structure is not None
        struct: ProjectStructure = res.structure
        assert struct.total_files == 3
        assert struct.primary_language == "py"
        assert "main.py" in struct.entry_points
        assert "sub" in struct.key_directories


def test_filesystem_path_traversal_blocked():
    """Verify path traversal outside permitted base directory is strictly blocked."""
    with tempfile.TemporaryDirectory() as tmpdir:
        fs = FilesystemCapability(base_dir=tmpdir)
        # Attempt to escape workspace
        res = fs.read_code_file("/etc/passwd")
        assert res.success is False
        assert "Path traversal outside permitted workspace" in str(res.error)


def test_filesystem_secret_file_protection():
    """Verify reading .env, credentials, or private keys is unconditionally rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        env_file = root / ".env"
        env_file.write_text("SECRET_KEY=12345", encoding="utf-8")

        key_file = root / "id_rsa"
        key_file.write_text("PRIVATE KEY DATA", encoding="utf-8")

        fs = FilesystemCapability(base_dir=str(root))

        res_env = fs.read_code_file(str(env_file))
        assert res_env.success is False
        assert "Security block: Reading secret or credential file" in str(res_env.error)

        res_key = fs.read_code_file(str(key_file))
        assert res_key.success is False
        assert "Security block: Reading secret or credential file" in str(res_key.error)


def test_filesystem_symbol_search():
    """Verify symbol search accurately locates functions in permitted project code."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "tree.py").write_text(
            "class BinaryTree:\n    def search_node(self, val):\n        return True\n",
            encoding="utf-8",
        )

        fs = FilesystemCapability(base_dir=str(root))
        res = fs.search_symbols("search_node")
        assert res.success is True
        assert len(res.matches) == 1
        assert res.matches[0]["file"] == "tree.py"
        assert "search_node" in res.matches[0]["match"]
