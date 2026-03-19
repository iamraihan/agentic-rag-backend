import logging
from pathlib import Path

from pypdf import PdfReader

from app.core.exceptions import UnsupportedFileTypeError

logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md"}


def extract_text(file_path: Path) -> str:
    suffix = file_path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise UnsupportedFileTypeError(suffix)

    if suffix == ".pdf":
        return _load_pdf(file_path)
    return _load_text(file_path)


def _load_pdf(file_path: Path) -> str:
    reader = PdfReader(file_path)
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    full_text = "\n\n".join(pages)
    logger.info("Extracted %d pages from PDF: %s", len(pages), file_path.name)
    return full_text


def _load_text(file_path: Path) -> str:
    text = file_path.read_text(encoding="utf-8")
    logger.info("Loaded text file: %s (%d chars)", file_path.name, len(text))
    return text
