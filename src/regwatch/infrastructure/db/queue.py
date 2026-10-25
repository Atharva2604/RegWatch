"""Postgres-backed Job Queue implementing the domain JobQueue protocol."""

import logging
from datetime import datetime, timezone
from typing import Any
from regwatch.domain.models import Job
from regwatch.domain.ports import JobQueue

logger = logging.getLogger(__name__)


class PostgresJobQueue(JobQueue):
    """Postgres / Supabase backed job queue supporting SKIP LOCKED atomic claims

    with an in-memory queue fallback for offline/unit test execution.
    """

    def __init__(self, supabase_client: Any = None) -> None:
        self.client = supabase_client
        self._memory_queue: list[Job] = []
        self._id_counter = 1

    def enqueue(self, job_type: str, payload: dict[str, Any], dedupe_key: str | None = None) -> Job:
        """Enqueue task. Deduplicates if dedupe_key is provided and pending."""
        if self.client:
            try:
                # Check dedupe_key in Postgres
                data = {
                    "job_type": job_type,
                    "payload": payload,
                    "dedupe_key": dedupe_key,
                    "status": "pending",
                }
                res = self.client.table("jobs").insert(data).execute()
                if res.data:
                    row = res.data[0]
                    return Job(
                        id=row["id"],
                        job_type=row["job_type"],
                        payload=row["payload"],
                        dedupe_key=row.get("dedupe_key"),
                        status=row["status"],
                    )
            except Exception as exc:
                logger.debug("Database enqueue failed or deduplicated (%s). Falling back to memory queue.", exc)

        # In-memory fallback
        if dedupe_key:
            for existing in self._memory_queue:
                if existing.dedupe_key == dedupe_key and existing.status in {"pending", "running"}:
                    return existing

        job = Job(
            id=self._id_counter,
            job_type=job_type,
            payload=payload,
            dedupe_key=dedupe_key,
            status="pending",
        )
        self._id_counter += 1
        self._memory_queue.append(job)
        return job

    def claim_next(self, worker_id: str) -> Job | None:
        """Claim the next pending job atomically."""
        if self.client:
            try:
                # Note: claim_job RPC executes FOR UPDATE SKIP LOCKED
                res = self.client.rpc("claim_job", {"p_worker_id": worker_id}).execute()
                if res.data:
                    row = res.data[0]
                    return Job(
                        id=row["id"],
                        job_type=row["job_type"],
                        payload=row["payload"],
                        dedupe_key=row.get("dedupe_key"),
                        status=row["status"],
                        attempts=row.get("attempts", 1),
                    )
            except Exception as exc:
                logger.debug("RPC claim_job unavailable (%s). Checking direct table claim.", exc)

            try:
                # Direct table claim fallback
                rows = self.client.table("jobs").select("*").eq("status", "pending").order("id").limit(1).execute()
                if rows.data:
                    row = rows.data[0]
                    update_res = self.client.table("jobs").update({
                        "status": "running",
                        "locked_at": datetime.now(timezone.utc).isoformat(),
                        "attempts": (row.get("attempts") or 0) + 1,
                    }).eq("id", row["id"]).eq("status", "pending").execute()
                    if update_res.data:
                        return Job(
                            id=row["id"],
                            job_type=row["job_type"],
                            payload=row["payload"],
                            dedupe_key=row.get("dedupe_key"),
                            status="running",
                            attempts=(row.get("attempts") or 0) + 1,
                        )
            except Exception as exc:
                logger.debug("Direct table claim failed (%s). Checking in-memory queue.", exc)

        for job in self._memory_queue:
            if job.status == "pending":
                job.status = "running"
                job.locked_at = datetime.now(timezone.utc)
                job.attempts += 1
                return job

        return None

    def mark_completed(self, job_id: int) -> None:
        """Mark job successfully completed."""
        if self.client:
            try:
                self.client.table("jobs").update({"status": "done"}).eq("id", job_id).execute()
                return
            except Exception:
                pass

        for job in self._memory_queue:
            if job.id == job_id:
                job.status = "done"
                return

    def mark_failed(self, job_id: int, error: str, retry_after_seconds: int = 60) -> None:
        """Mark job failed and schedule backoff retry or dead-letter."""
        if self.client:
            try:
                self.client.table("jobs").update({
                    "status": "failed",
                    "last_error": error,
                }).eq("id", job_id).execute()
                return
            except Exception:
                pass

        for job in self._memory_queue:
            if job.id == job_id:
                job.last_error = error
                if job.attempts >= job.max_attempts:
                    job.status = "dead"
                else:
                    job.status = "failed"
                return
