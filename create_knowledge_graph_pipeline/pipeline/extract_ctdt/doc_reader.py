"""Read CTDT source documents into plain text for LLM extraction."""

from __future__ import annotations

from pathlib import Path


SUPPORTED_SUFFIXES = {".md", ".txt", ".pdf"}


def read_source_text(path: Path) -> str:
    suffix = path.suffix.casefold()
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8")
    if suffix == ".pdf":
        return _read_pdf_text(path)
    raise ValueError(f"Unsupported CTDT input type: {path.suffix}")


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF CTDT input requires pypdf. Install requirements.txt first.") from exc

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n\n".join(page.strip() for page in pages if page.strip())
    if not text:
        raise ValueError(f"No extractable text found in {path}")
    return text

