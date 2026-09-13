"""
Filesystem Learning Capability Subsystem.
Enables project-based learning and codebase exploration with strict path traversal defense,
secret file masking (.env, ssh keys, tokens), and gated write permissions.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent
from tarkyaan.safety.permissions import PermissionCategory, PermissionManager, permission_manager


class FileMetadata(BaseModel):
    """Metadata of an inspected source file."""
    path: str
    relative_path: str
    size_bytes: int
    language: str
    line_count: int = 0


class ProjectStructure(BaseModel):
    """Summary of a learning project codebase."""
    root_path: str
    project_name: str
    primary_language: str
    total_files: int
    files: List[FileMetadata] = Field(default_factory=list)
    key_directories: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)


class FilesystemActionResult(BaseModel):
    """Outcome of a filesystem operation."""
    success: bool
    operation: str
    target_path: str
    content: Optional[str] = None
    structure: Optional[ProjectStructure] = None
    matches: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None


class FilesystemCapability:
    """
    Filesystem capability for codebase learning.
    Default: READ-ONLY. Blocks path traversal outside permitted workspace and blocks secret files.
    """

    # Protected files and secrets that must NEVER be read or exposed
    BLOCKED_PATTERNS = [
        r"^\.env(\..+)?$",
        r".*\.pem$",
        r".*\.key$",
        r"id_rsa.*",
        r"credentials\.json",
        r".*\.pfx$",
        r".*token.*\.json",
    ]

    ALLOWED_EXTENSIONS = {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".c", ".cpp", ".h",
        ".rs", ".go", ".html", ".css", ".md", ".txt", ".json", ".yaml", ".yml",
        ".toml", ".sh", ".sql"
    }

    def __init__(
        self,
        base_dir: Optional[str] = None,
        perms: Optional[PermissionManager] = None,
        event_bus: Optional[EventBus] = None,
    ) -> None:
        self.base_dir = Path(base_dir or os.getcwd()).resolve()
        self.permission_mgr = perms or permission_manager
        self.event_bus = event_bus

    def inspect_project_structure(
        self,
        directory_path: Optional[str] = None,
        max_files: int = 50,
    ) -> FilesystemActionResult:
        """
        Scan a permitted project directory and map its architectural layout.
        Bounded traversal to avoid indexing huge node_modules or .git directories.
        """
        target = Path(directory_path).resolve() if directory_path else self.base_dir
        if not self._is_path_safe(target):
            return FilesystemActionResult(
                success=False,
                operation="inspect_project",
                target_path=str(target),
                error="Security block: Path traversal outside permitted workspace.",
            )

        if not target.exists() or not target.is_dir():
            return FilesystemActionResult(
                success=False,
                operation="inspect_project",
                target_path=str(target),
                error=f"Directory does not exist: {target}",
            )

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.FILESYSTEM_ACTION_STARTED,
                {"operation": "inspect_project", "path": str(target)},
            )

        file_list: List[FileMetadata] = []
        key_dirs = set()
        entry_points = []
        lang_counts: Dict[str, int] = {}

        ignored_dirs = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "build", "dist"}

        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in ignored_dirs]
            rel_root = os.path.relpath(root, target)
            if rel_root != ".":
                key_dirs.add(rel_root.split(os.sep)[0])

            for f in files:
                if len(file_list) >= max_files:
                    break
                if self._is_secret_file(f):
                    continue

                fpath = Path(root) / f
                ext = fpath.suffix.lower()
                if ext in self.ALLOWED_EXTENSIONS:
                    try:
                        sz = fpath.stat().st_size
                        lang = ext.lstrip(".")
                        lang_counts[lang] = lang_counts.get(lang, 0) + 1
                        file_list.append(
                            FileMetadata(
                                path=str(fpath),
                                relative_path=str(fpath.relative_to(target)),
                                size_bytes=sz,
                                language=lang,
                            )
                        )
                        if f in ["main.py", "app.py", "index.js", "index.ts", "__main__.py"]:
                            entry_points.append(str(fpath.relative_to(target)))
                    except Exception:
                        pass

        primary_lang = max(lang_counts.items(), key=lambda x: x[1])[0] if lang_counts else "python"

        proj = ProjectStructure(
            root_path=str(target),
            project_name=target.name,
            primary_language=primary_lang,
            total_files=len(file_list),
            files=file_list,
            key_directories=sorted(list(key_dirs)),
            entry_points=entry_points,
        )

        return FilesystemActionResult(
            success=True,
            operation="inspect_project",
            target_path=str(target),
            structure=proj,
        )

    def read_code_file(
        self,
        file_path: str,
        max_lines: int = 500,
    ) -> FilesystemActionResult:
        """
        Read code file content with strict safety, path traversal checks, and bounded lines.
        """
        path = Path(file_path).resolve()
        if not self._is_path_safe(path):
            return FilesystemActionResult(
                success=False,
                operation="read_file",
                target_path=str(path),
                error="Security block: Path traversal outside permitted workspace.",
            )

        if self._is_secret_file(path.name):
            return FilesystemActionResult(
                success=False,
                operation="read_file",
                target_path=str(path),
                error=f"Security block: Reading secret or credential file '{path.name}' is strictly forbidden.",
            )

        if not path.exists() or not path.is_file():
            return FilesystemActionResult(
                success=False,
                operation="read_file",
                target_path=str(path),
                error=f"File not found: {path}",
            )

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            bounded_content = "\n".join(lines[:max_lines])
            return FilesystemActionResult(
                success=True,
                operation="read_file",
                target_path=str(path),
                content=bounded_content,
            )
        except Exception as e:
            return FilesystemActionResult(
                success=False,
                operation="read_file",
                target_path=str(path),
                error=f"Error reading file: {str(e)}",
            )

    def search_symbols(
        self,
        symbol_query: str,
        directory_path: Optional[str] = None,
        max_matches: int = 15,
    ) -> FilesystemActionResult:
        """Search for class, function, or variable definitions across permitted project files."""
        target = Path(directory_path).resolve() if directory_path else self.base_dir
        if not self._is_path_safe(target):
            return FilesystemActionResult(
                success=False,
                operation="search_symbols",
                target_path=str(target),
                error="Security block: Path traversal outside permitted workspace.",
            )

        matches = []
        pattern = re.compile(rf"(def|class|function|fn|var|let|const)\s+([a-zA-Z0-9_]*{symbol_query}[a-zA-Z0-9_]*)", re.IGNORECASE)

        for root, dirs, files in os.walk(target):
            dirs[:] = [d for d in dirs if d not in {".git", ".venv", "node_modules", "__pycache__"}]
            for f in files:
                if self._is_secret_file(f):
                    continue
                fpath = Path(root) / f
                if fpath.suffix.lower() in self.ALLOWED_EXTENSIONS:
                    try:
                        content_lines = fpath.read_text(encoding="utf-8", errors="ignore").splitlines()
                        for i, line in enumerate(content_lines[:300]):
                            m = pattern.search(line)
                            if m:
                                matches.append({
                                    "file": str(fpath.relative_to(target)),
                                    "line": i + 1,
                                    "match": line.strip(),
                                })
                                if len(matches) >= max_matches:
                                    break
                    except Exception:
                        pass
                if len(matches) >= max_matches:
                    break

        return FilesystemActionResult(
            success=True,
            operation="search_symbols",
            target_path=str(target),
            matches=matches,
        )

    def _is_path_safe(self, path: Path) -> bool:
        """Verify that the path does not escape the base directory (path traversal check)."""
        try:
            # Must either resolve within base_dir or be a subdirectory
            path.relative_to(self.base_dir)
            return True
        except ValueError:
            # Check if path is within project directory
            return False

    def _is_secret_file(self, filename: str) -> bool:
        """Check if filename matches any protected secret patterns."""
        for pat in self.BLOCKED_PATTERNS:
            if re.match(pat, filename, re.IGNORECASE):
                return True
        return False
