import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TextChunk:
    content: str
    chunk_index: int


def split_text(
    text: str,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> list[TextChunk]:
    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks = _recursive_split(text, separators, chunk_size, chunk_overlap)
    result = [TextChunk(content=c, chunk_index=i) for i, c in enumerate(chunks)]
    logger.info(
        "Split text into %d chunks (size=%d, overlap=%d)", len(result), chunk_size, chunk_overlap
    )
    return result


def _recursive_split(
    text: str,
    separators: list[str],
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    if not text:
        return []

    final_chunks: list[str] = []
    separator = separators[-1]

    for sep in separators:
        if sep in text:
            separator = sep
            break

    splits = text.split(separator) if separator else list(text)

    current_chunk: list[str] = []
    current_length = 0

    for piece in splits:
        piece_len = len(piece) + (len(separator) if current_chunk else 0)

        if current_length + piece_len > chunk_size and current_chunk:
            chunk_text = separator.join(current_chunk)
            final_chunks.append(chunk_text)

            # Keep overlap
            while current_length > chunk_overlap and current_chunk:
                removed = current_chunk.pop(0)
                current_length -= len(removed) + len(separator)

        current_chunk.append(piece)
        current_length += piece_len

    if current_chunk:
        final_chunks.append(separator.join(current_chunk))

    return final_chunks
