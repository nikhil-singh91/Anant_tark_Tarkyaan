"""
Document Understanding Subsystem.
Extracts, chunks, indexes, and normalizes educational documents (PDF, Markdown, TXT, Code).
Enforces bounded context retrieval rather than dumping raw documents into prompts.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tarkyaan.events.event_bus import EventBus, TarkyaanEvent


class DocumentSection(BaseModel):
    """A bounded structural section or chunk of an educational document."""
    section_index: int
    title: str
    content: str
    word_count: int
    key_terms: List[str] = Field(default_factory=list)


class DocumentOutline(BaseModel):
    """High-level index and pedagogical structure of a parsed document."""
    file_path: str
    file_type: str
    total_sections: int
    total_word_count: int
    sections: List[DocumentSection] = Field(default_factory=list)
    detected_topics: List[str] = Field(default_factory=list)
    summary: str = ""


class DocumentUnderstandingEngine:
    """
    Pedagogical document parser and bounded chunk retriever.
    Supports learning from PDFs, Markdown, TXT, and source code files.
    """

    def __init__(self, event_bus: Optional[EventBus] = None) -> None:
        self.event_bus = event_bus

    def parse_document(
        self,
        file_path: str | Path,
        max_chunk_words: int = 400,
    ) -> DocumentOutline:
        """
        Extract and chunk an educational document with structural headers.
        Employs bounded chunking to keep context windows lean.
        """
        path = Path(file_path)
        if not path.exists():
            return DocumentOutline(
                file_path=str(file_path),
                file_type="unknown",
                total_sections=0,
                total_word_count=0,
                summary=f"Error: File not found at {file_path}",
            )

        suffix = path.suffix.lower()
        content = ""

        if suffix in [".txt", ".md", ".py", ".js", ".java", ".cpp", ".c", ".rs", ".go", ".html", ".json"]:
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                content = f"Error reading text document: {e}"
        elif suffix == ".pdf":
            content = self._extract_pdf_text(path)
        else:
            # General binary or unhandled
            content = f"Unsupported document format: {suffix}"

        sections = self._chunk_content(content, max_chunk_words=max_chunk_words)
        detected_topics = self._extract_keywords(content)
        total_words = sum(s.word_count for s in sections)

        summary_preview = (
            f"Document {path.name} contains {len(sections)} sections covering: {', '.join(detected_topics[:5])}."
        )

        outline = DocumentOutline(
            file_path=str(path.resolve()),
            file_type=suffix.lstrip("."),
            total_sections=len(sections),
            total_word_count=total_words,
            sections=sections,
            detected_topics=detected_topics,
            summary=summary_preview,
        )

        if self.event_bus:
            self.event_bus.publish(
                TarkyaanEvent.DOCUMENT_PARSED,
                {
                    "file_path": str(path.name),
                    "file_type": outline.file_type,
                    "sections": outline.total_sections,
                    "topics": detected_topics[:5],
                },
            )

        return outline

    def get_relevant_sections(
        self,
        outline: DocumentOutline,
        query_or_topic: str,
        max_sections: int = 3,
    ) -> List[DocumentSection]:
        """
        Bounded retrieval: Retrieve only the top-K relevant chunks for a given topic or question.
        Prevents context bloating in the LLM.
        """
        if not outline.sections:
            return []

        query_tokens = set(re.findall(r"\w+", query_or_topic.lower()))
        scored_sections = []

        for sec in outline.sections:
            sec_text = (sec.title + " " + sec.content).lower()
            sec_tokens = set(re.findall(r"\w+", sec_text))
            overlap = len(query_tokens.intersection(sec_tokens))
            scored_sections.append((overlap, sec))

        scored_sections.sort(key=lambda x: x[0], reverse=True)
        # Return top matches
        return [sec for _, sec in scored_sections[:max_sections]]

    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF using pypdf if available, or fallback."""
        try:
            import pypdf
            reader = pypdf.PdfReader(str(path))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append(f"--- Page {i+1} ---\n{text}")
            return "\n\n".join(pages)
        except ImportError:
            # If pypdf is not installed in the environment, fallback to structured reader or string scan
            return self._fallback_pdf_read(path)
        except Exception as e:
            return f"Error extracting PDF: {str(e)}"

    def _fallback_pdf_read(self, path: Path) -> str:
        """Fallback for PDF reading when external libraries are not present."""
        try:
            raw = path.read_bytes()
            # Simple text extraction for plaintext streams inside PDF
            text_parts = re.findall(b"[(](.*?)[)]", raw)
            decoded = [p.decode("latin-1", errors="ignore") for p in text_parts if len(p) > 3]
            if decoded:
                return "\n".join(decoded[:200])
        except Exception:
            pass
        return f"PDF document: {path.name} (Binary content loaded, pypdf recommended for full extraction)."

    def _chunk_content(self, text: str, max_chunk_words: int) -> List[DocumentSection]:
        """Split document text into bounded sections by headers or paragraphs."""
        lines = text.split("\n")
        sections: List[DocumentSection] = []
        curr_title = "Introduction / Overview"
        curr_words: List[str] = []
        sec_idx = 1

        for line in lines:
            line_str = line.strip()
            # Detect Markdown / structural headers
            if line_str.startswith(("#", "===", "---", "Page ", "Chapter ", "Section ")) and curr_words:
                content_str = " ".join(curr_words)
                words = content_str.split()
                if words:
                    sections.append(
                        DocumentSection(
                            section_index=sec_idx,
                            title=curr_title,
                            content=content_str,
                            word_count=len(words),
                            key_terms=self._extract_keywords(content_str)[:5],
                        )
                    )
                    sec_idx += 1
                curr_title = line_str.lstrip("#-=\t ") or f"Section {sec_idx}"
                curr_words = []
            else:
                curr_words.append(line)
                if len(" ".join(curr_words).split()) >= max_chunk_words:
                    content_str = " ".join(curr_words)
                    sections.append(
                        DocumentSection(
                            section_index=sec_idx,
                            title=curr_title,
                            content=content_str,
                            word_count=len(content_str.split()),
                            key_terms=self._extract_keywords(content_str)[:5],
                        )
                    )
                    sec_idx += 1
                    curr_title = f"Section {sec_idx} (Continued)"
                    curr_words = []

        if curr_words:
            content_str = " ".join(curr_words)
            words = content_str.split()
            if words:
                sections.append(
                    DocumentSection(
                        section_index=sec_idx,
                        title=curr_title,
                        content=content_str,
                        word_count=len(words),
                        key_terms=self._extract_keywords(content_str)[:5],
                    )
                )

        return sections

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract frequent domain-specific keywords from text."""
        tokens = re.findall(r"\b[a-zA-Z]{4,}\b", text.lower())
        stopwords = {
            "this", "that", "with", "from", "have", "more", "then", "when",
            "some", "such", "into", "than", "other", "also", "been", "were",
            "will", "about", "which", "there", "these", "their", "after"
        }
        filtered = [t for t in tokens if t not in stopwords]
        freq: Dict[str, int] = {}
        for f in filtered:
            freq[f] = freq.get(f, 0) + 1
        sorted_kws = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [k for k, _ in sorted_kws[:12]]
