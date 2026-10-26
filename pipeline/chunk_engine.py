"""
RegWatch Pipeline — Chunk Engine & Multi-Vector Hierarchical Retrieval
Solves the document truncation loophole by storing and querying clause-level
384-dimensional embeddings (500 tokens with 50-token overlap) in regulation_chunks.
"""
import os
import json
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer
from pipeline.chunk_utils import split_into_sliding_chunks

load_dotenv()
logger = logging.getLogger("regwatch.chunk_engine")

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

_model: Optional[SentenceTransformer] = None


def get_embedding_model() -> SentenceTransformer:
    """Lazily load and cache the 384-dim SentenceTransformer model."""
    global _model
    if _model is None:
        logger.info("Initializing embedding model: all-MiniLM-L6-v2 (384-dim)")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def chunk_and_index_regulation(
    regulation_id: int,
    content_text: str,
    title: str = "",
    batch_size: int = 25,
) -> int:
    """
    Chunks a circular using 500-token sliding windows with 50-token overlap,
    generates 384-dim embeddings, and persists them into regulation_chunks.

    Parameters:
        regulation_id: Primary key of the parent regulation.
        content_text: Full body text of the circular (not truncated).
        title: Title of circular for embedding context prefix.
        batch_size: Supabase batch insertion limit.

    Returns:
        Total number of chunks indexed in Supabase.
    """
    if not content_text or len(content_text.strip()) < 40:
        return 0

    # 1. Generate sliding chunks (500 tokens with 50-token overlap)
    chunks = split_into_sliding_chunks(
        content_text,
        chunk_size_tokens=500,
        overlap_tokens=50,
        min_chunk_tokens=40
    )
    if not chunks:
        return 0

    model = get_embedding_model()

    # 2. Check if already chunked; purge existing chunks for idempotency
    try:
        existing = (
            supabase.table("regulation_chunks")
            .select("id")
            .eq("regulation_id", regulation_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            supabase.table("regulation_chunks").delete().eq("regulation_id", regulation_id).execute()
    except Exception as e:
        logger.warning(f"Error checking existing chunks for reg {regulation_id}: {e}")

    # 3. Batch encode chunk texts with title context
    texts_to_embed = [
        f"{title}: {c['text'][:1500]}" if title else c["text"][:1500]
        for c in chunks
    ]
    embeddings = model.encode(texts_to_embed, normalize_embeddings=True, show_progress_bar=False)

    rows = []
    for idx, c in enumerate(chunks):
        rows.append({
            "regulation_id": regulation_id,
            "chunk_index": c["chunk_index"],
            "text": c["text"],
            "embedding": embeddings[idx].tolist(),
            "embedding_model": "all-MiniLM-L6-v2",
        })

    # 4. Batch insert into regulation_chunks table
    total_inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i + batch_size]
        try:
            supabase.table("regulation_chunks").insert(batch).execute()
            total_inserted += len(batch)
        except Exception as insert_err:
            logger.error(f"Failed inserting chunk batch for regulation {regulation_id}: {insert_err}")
            raise insert_err

    logger.info(f"Indexed {total_inserted} chunks for regulation #{regulation_id} ({title[:60]})")
    return total_inserted


def find_governing_chunks(
    query_text: str,
    top_k: int = 5,
    query_embedding: Optional[List[float]] = None,
    min_similarity: float = 0.15,
) -> List[Dict[str, Any]]:
    """
    Performs clause-level semantic retrieval over regulation_chunks.
    Matches company policies against individual circular clauses rather than truncated headers.

    Parameters:
        query_text: The policy text or compliance query.
        top_k: Number of highest-relevance statutory clauses to return.
        query_embedding: Optional pre-computed 384-dim embedding vector.
        min_similarity: Minimum cosine similarity threshold.

    Returns:
        List of matched statutory clauses with parent regulation metadata and similarity scores.
    """
    model = get_embedding_model()
    if query_embedding is None:
        q_emb = model.encode(query_text[:1500], normalize_embeddings=True)
    else:
        q_emb = np.array(query_embedding, dtype=np.float32)

    # 1. Attempt Supabase match RPC if configured on chunks
    try:
        rpc_res = supabase.rpc("match_regulation_chunks", {
            "query_embedding": q_emb.tolist(),
            "match_count": top_k,
        }).execute()
        if rpc_res.data and len(rpc_res.data) > 0:
            return rpc_res.data
    except Exception:
        pass

    # 2. Local Cosine Similarity over regulation_chunks
    try:
        chunks_res = (
            supabase.table("regulation_chunks")
            .select("id, regulation_id, chunk_index, text, embedding")
            .limit(1000)
            .execute()
        )
        raw_chunks = chunks_res.data or []
    except Exception as fetch_err:
        logger.warning(f"Failed to query regulation_chunks: {fetch_err}")
        raw_chunks = []

    if not raw_chunks:
        return []

    valid_chunks = []
    chunk_vectors = []

    for c in raw_chunks:
        emb = c.get("embedding")
        if emb:
            if isinstance(emb, str):
                emb = json.loads(emb)
            valid_chunks.append(c)
            chunk_vectors.append(emb)

    if not chunk_vectors:
        return []

    # Normalized dot product = cosine similarity
    C = np.array(chunk_vectors, dtype=np.float32)
    scores = np.dot(C, q_emb)
    ranked_indices = np.argsort(scores)[::-1]

    # Filter by minimum similarity and top_k
    top_indices = [idx for idx in ranked_indices if scores[idx] >= min_similarity][:top_k]
    if not top_indices and len(ranked_indices) > 0:
        top_indices = ranked_indices[:top_k]

    # Fetch parent regulation metadata
    reg_ids = list(set(valid_chunks[idx]["regulation_id"] for idx in top_indices))
    reg_map = {}
    if reg_ids:
        try:
            r_res = (
                supabase.table("regulations")
                .select("id, title, reference_number, published_date, department, url")
                .in_("id", reg_ids)
                .execute()
            )
            for r in r_res.data or []:
                reg_map[r["id"]] = r
        except Exception as e:
            logger.warning(f"Error fetching parent regulations: {e}")

    results = []
    for idx in top_indices:
        item = dict(valid_chunks[idx])
        item["similarity"] = float(scores[idx])
        item["regulation"] = reg_map.get(item["regulation_id"], {})
        item.pop("embedding", None)
        results.append(item)

    return results
