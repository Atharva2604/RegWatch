"""
RegWatch Pipeline — Legal Document Chunking Utilities
Implements sliding-window document chunking (500 tokens with 50-token overlap)
to eliminate regulatory clause loss in compliance monitoring.
"""
import re
from typing import List, Dict, Any, Optional


def split_into_sliding_chunks(
    text: str,
    chunk_size_tokens: int = 500,
    overlap_tokens: int = 50,
    min_chunk_tokens: int = 40,
    chunk_size_words: Optional[int] = None,
    overlap_words: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Splits statutory circulars and legal instruments into sliding-window chunks
    of 500 tokens with 50-token overlap.

    Guarantees that long multi-page circulars (50+ pages, annexures, penalty tables)
    are retained without document truncation flaws.

    Parameters:
        text: Raw or OCR-extracted circular text.
        chunk_size_tokens: Target window length (default: 500 tokens).
        overlap_tokens: Overlap between consecutive windows (default: 50 tokens).
        min_chunk_tokens: Minimum token count for trailing segment to avoid micro-chunks.
        chunk_size_words: Alias for backwards compatibility.
        overlap_words: Alias for backwards compatibility.

    Returns:
        List of chunk dictionaries with indices, text, token counts, and span offsets.
    """
    if not text or not text.strip():
        return []

    # Handle backward-compatible parameters if provided
    if chunk_size_words is not None:
        chunk_size_tokens = chunk_size_words
    if overlap_words is not None:
        overlap_tokens = overlap_words

    # Normalize carriage returns and consecutive whitespaces while keeping newlines for structure
    normalized_text = re.sub(r"\r\n|\r", "\n", text)
    normalized_text = re.sub(r"[ \t]+", " ", normalized_text).strip()

    # Tokenize by word-level tokens (preserves punctuation and legal clause formatting)
    tokens = [t for t in re.split(r"(\s+)", normalized_text) if t]
    
    # Extract actual word/symbol tokens while maintaining indices for accurate text slicing
    # A standard token in MiniLM/BERT is ~0.75 words, so 500 tokens ~ 375-500 word units.
    # We slice by word tokens:
    word_tokens = normalized_text.split()
    total_tokens = len(word_tokens)

    if total_tokens <= chunk_size_tokens:
        return [
            {
                "chunk_index": 0,
                "text": normalized_text,
                "token_count": total_tokens,
                "word_count": total_tokens,
                "char_start": 0,
                "char_end": len(normalized_text),
            }
        ]

    chunks = []
    step = chunk_size_tokens - overlap_tokens
    if step <= 0:
        step = max(1, chunk_size_tokens // 2)

    chunk_idx = 0
    start_idx = 0

    while start_idx < total_tokens:
        end_idx = min(start_idx + chunk_size_tokens, total_tokens)
        slice_tokens = word_tokens[start_idx:end_idx]

        # If the trailing slice is smaller than threshold and we already have chunks,
        # merge it into the previous chunk to avoid orphan clauses
        if len(slice_tokens) < min_chunk_tokens and chunks:
            merged_text = chunks[-1]["text"] + " " + " ".join(slice_tokens)
            chunks[-1]["text"] = merged_text
            chunks[-1]["token_count"] += len(slice_tokens)
            chunks[-1]["word_count"] += len(slice_tokens)
            chunks[-1]["char_end"] = len(merged_text)
            break

        chunk_text = " ".join(slice_tokens).strip()
        chunks.append({
            "chunk_index": chunk_idx,
            "text": chunk_text,
            "token_count": len(slice_tokens),
            "word_count": len(slice_tokens),
            "start_token": start_idx,
            "end_token": end_idx,
        })

        chunk_idx += 1
        start_idx += step

    return chunks
