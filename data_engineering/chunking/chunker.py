import logging
from dataclasses import dataclass
from typing import List

from data_engineering.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class TextChunk:
    chunk_index: int
    text: str
    token_count: int
    char_start: int
    char_end: int


class TextChunker:
    """
    Splits masked text into overlapping token-bounded chunks.
    Uses tiktoken when available; falls back to whitespace approx (~4 chars/token).
    """

    def __init__(self):
        settings = get_settings()
        self.chunk_size = settings.chunk_size_tokens
        self.overlap = settings.chunk_overlap_tokens
        self._encoder = None
        try:
            import tiktoken

            self._encoder = tiktoken.get_encoding("cl100k_base")
        except Exception as exc:
            logger.warning("tiktoken unavailable (%s); using char approx chunker", exc)

    def _encode(self, text: str) -> List[int]:
        if self._encoder is not None:
            return self._encoder.encode(text)
        # Approximate tokens as 4-char windows for offline checkout
        return list(range(max(1, (len(text) + 3) // 4)))

    def _decode_slice(self, text: str, start_tok: int, end_tok: int) -> str:
        if self._encoder is not None:
            tokens = self._encoder.encode(text)
            return self._encoder.decode(tokens[start_tok:end_tok])
        start_char = start_tok * 4
        end_char = min(len(text), end_tok * 4)
        return text[start_char:end_char]

    def chunk(self, masked_text: str) -> List[TextChunk]:
        if not masked_text or not masked_text.strip():
            return []

        if self._encoder is not None:
            tokens = self._encoder.encode(masked_text)
            total_tokens = len(tokens)
        else:
            total_tokens = max(1, (len(masked_text) + 3) // 4)

        chunks: List[TextChunk] = []
        chunk_index = 0
        start = 0
        step = max(1, self.chunk_size - self.overlap)

        while start < total_tokens:
            end = min(start + self.chunk_size, total_tokens)
            if self._encoder is not None:
                chunk_tokens = tokens[start:end]
                chunk_text = self._encoder.decode(chunk_tokens)
                prefix_text = self._encoder.decode(tokens[:start])
                char_start = len(prefix_text)
                char_end = char_start + len(chunk_text)
                token_count = len(chunk_tokens)
            else:
                chunk_text = self._decode_slice(masked_text, start, end)
                char_start = start * 4
                char_end = min(len(masked_text), end * 4)
                token_count = end - start

            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    text=chunk_text,
                    token_count=token_count,
                    char_start=char_start,
                    char_end=char_end,
                )
            )
            chunk_index += 1
            start += step

        logger.info(
            "chunking_complete total_tokens=%s chunk_count=%s",
            total_tokens,
            len(chunks),
        )
        return chunks
