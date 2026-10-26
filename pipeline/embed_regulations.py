"""
Batch-embeds all SEBI regulations in Supabase using all-MiniLM-L6-v2 (384 dims).
Uses batch model encoding and multi-threaded database updates for maximum speed.
"""
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase import create_client
from sentence_transformers import SentenceTransformer

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_FETCH_SIZE = 200
NUM_WORKERS = 10


def update_single_embedding(reg_id, embedding_list):
    try:
        supabase.table("regulations").update(
            {"embedding": embedding_list}
        ).eq("id", reg_id).execute()
        return True
    except Exception as e:
        print(f"Error updating reg {reg_id}: {e}")
        return False


def main():
    print(f"Loading embedding model ({MODEL_NAME})...")
    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.\n")

    unembedded_count = (
        supabase.table("regulations")
        .select("id", count="exact")
        .is_("embedding", "null")
        .execute()
        .count
    )

    print(f"Regulations to embed: {unembedded_count}")
    if unembedded_count == 0:
        print("All regulations are already embedded!")
        return

    total_processed = 0
    start_time = time.time()

    while True:
        regs = (
            supabase.table("regulations")
            .select("id, title, content_text")
            .is_("embedding", "null")
            .limit(BATCH_FETCH_SIZE)
            .execute()
            .data
        )

        if not regs:
            break

        texts = []
        reg_ids = []
        for r in regs:
            title = r.get("title") or "SEBI Circular"
            content = r.get("content_text") or ""
            text = f"{title}. {content[:1500]}"
            texts.append(text)
            reg_ids.append(r["id"])

        embeddings = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=False,
            normalize_embeddings=True
        )

        with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = [
                executor.submit(update_single_embedding, reg_id, emb.tolist())
                for reg_id, emb in zip(reg_ids, embeddings)
            ]
            for f in as_completed(futures):
                pass

        # Index 500-token chunks into regulation_chunks for each regulation
        try:
            from pipeline.chunk_engine import chunk_and_index_regulation
            for r in regs:
                if r.get("content_text"):
                    chunk_and_index_regulation(r["id"], r["content_text"], title=r.get("title", ""))
        except Exception as chunk_err:
            print(f"Warning indexing chunks: {chunk_err}")


        total_processed += len(regs)
        elapsed = time.time() - start_time
        rate = total_processed / elapsed if elapsed > 0 else 0
        print(f"Progress: [{total_processed}/{unembedded_count}] regulations embedded ({rate:.1f} regs/sec)...")

    total_time = time.time() - start_time
    print(f"\nFinished! Embedded {total_processed} regulations in {total_time:.1f} seconds.")


if __name__ == "__main__":
    main()
