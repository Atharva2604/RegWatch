"""
Unit Tests for Loophole 1: 500-Token Sliding-Window Document Chunking
Verifies token accounting, 50-token overlap, and clause preservation.
"""
from pipeline.chunk_utils import split_into_sliding_chunks


def test_split_into_sliding_chunks_under_window_size():
    short_text = "SEBI circular on client margin requirements. Margin collection mandatory before execution."
    chunks = split_into_sliding_chunks(short_text, chunk_size_tokens=500, overlap_tokens=50)
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["text"] == short_text
    assert chunks[0]["token_count"] == len(short_text.split())


def test_split_into_sliding_chunks_500_tokens_50_overlap():
    # Generate 1200 words of synthetic circular text
    words = [f"clause_{i}" for i in range(1200)]
    full_text = " ".join(words)

    chunks = split_into_sliding_chunks(full_text, chunk_size_tokens=500, overlap_tokens=50)

    # Step size is 500 - 50 = 450 tokens
    # Window 0: 0 to 500
    # Window 1: 450 to 950
    # Window 2: 900 to 1200 (300 tokens > min_chunk_tokens 40)
    assert len(chunks) == 3
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["token_count"] == 500
    assert chunks[1]["chunk_index"] == 1
    assert chunks[1]["token_count"] == 500

    # Verify overlap: last 50 tokens of chunk 0 should match first 50 tokens of chunk 1
    chunk_0_tokens = chunks[0]["text"].split()
    chunk_1_tokens = chunks[1]["text"].split()
    assert chunk_0_tokens[-50:] == chunk_1_tokens[:50]


def test_split_into_sliding_chunks_preserves_annexure_and_penalty_clauses():
    # Buried clause after 800 words
    preamble = " ".join(["preamble_word"] * 800)
    buried_clause = "ANNEXURE IV: Violation of KYC turnaround timelines attracts statutory penalty under Section 15HB."
    full_text = f"{preamble} {buried_clause}"

    chunks = split_into_sliding_chunks(full_text, chunk_size_tokens=500, overlap_tokens=50)

    # In old [:1000] char slicing, buried_clause was completely lost!
    # With sliding window, buried clause must be preserved in later chunk
    found = any("ANNEXURE IV" in c["text"] and "Section 15HB" in c["text"] for c in chunks)
    assert found, "Buried penalty clause in Annexure must not be truncated"
