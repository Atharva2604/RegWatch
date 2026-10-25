"""Supabase / Postgres implementations of Domain Repositories."""

import logging
from datetime import datetime
from typing import Any
from regwatch.domain.models import (
    Alert,
    CompanyPolicy,
    ComplianceCheck,
    DocumentVersion,
    LegalDocument,
    LegalType,
    Obligation,
    RiskScore,
    Verdict,
)
from regwatch.domain.ports import (
    CheckRepository,
    DocumentRepository,
    ObligationRepository,
    PolicyRepository,
)

logger = logging.getLogger(__name__)


class SupabaseDocumentRepository(DocumentRepository):
    """Repository managing regulations and version snapshots in Supabase."""

    def __init__(self, client: Any = None) -> None:
        self.client = client
        self._memory_docs: dict[str, LegalDocument] = {}
        self._memory_versions: dict[int, list[DocumentVersion]] = {}
        self._id_seq = 1
        self._ver_seq = 1

    def get_by_url(self, url: str) -> LegalDocument | None:
        if self.client:
            try:
                res = self.client.table("regulations").select("*").eq("url", url).execute()
                if res.data:
                    row = res.data[0]
                    return LegalDocument(
                        id=row["id"],
                        source_key=row.get("source_id") or "sebi",
                        url=row["url"],
                        title=row.get("title", ""),
                        legal_type=LegalType(row.get("legal_type", "circular")),
                        content_hash=row.get("content_hash", "") or "",
                        content_text=row.get("content_text", "") or "",
                        current_version_id=row.get("current_version_id"),
                    )
            except Exception as exc:
                logger.debug("Database select failed (%s). Falling back to memory store.", exc)

        return self._memory_docs.get(url)

    def save_document(self, document: LegalDocument) -> LegalDocument:
        if self.client:
            try:
                data = {
                    "title": document.title,
                    "url": document.url,
                    "legal_type": document.legal_type.value,
                    "content_hash": document.content_hash,
                    "content_text": document.content_text,
                    "last_checked_at": document.last_checked_at.isoformat() if document.last_checked_at else None,
                    "last_changed_at": document.last_changed_at.isoformat() if document.last_changed_at else None,
                }
                if document.current_version_id:
                    data["current_version_id"] = document.current_version_id

                if document.id:
                    res = self.client.table("regulations").update(data).eq("id", document.id).execute()
                else:
                    existing = self.client.table("regulations").select("id").eq("url", document.url).execute()
                    if existing.data:
                        document.id = existing.data[0]["id"]
                        res = self.client.table("regulations").update(data).eq("id", document.id).execute()
                    else:
                        res = self.client.table("regulations").insert(data).execute()

                if res.data:
                    document.id = res.data[0]["id"]
                    return document
            except Exception as exc:
                logger.debug("Database save_document failed (%s). Falling back to memory store.", exc)

        if not document.id:
            document.id = self._id_seq
            self._id_seq += 1
        self._memory_docs[document.url] = document
        return document

    def save_version(self, version: DocumentVersion) -> DocumentVersion:
        if self.client:
            try:
                data = {
                    "regulation_id": version.regulation_id,
                    "version_no": version.version_no,
                    "content_text": version.content_text,
                    "raw_sha256": version.raw_sha256,
                }
                res = self.client.table("regulation_versions").insert(data).execute()
                if res.data:
                    return DocumentVersion(
                        id=res.data[0]["id"],
                        regulation_id=version.regulation_id,
                        version_no=version.version_no,
                        content_text=version.content_text,
                        content_hash=version.content_hash,
                        raw_sha256=version.raw_sha256,
                    )
            except Exception as exc:
                logger.debug("Database save_version failed (%s). Falling back to memory store.", exc)

        saved_v = DocumentVersion(
            id=self._ver_seq,
            regulation_id=version.regulation_id,
            version_no=version.version_no,
            content_text=version.content_text,
            content_hash=version.content_hash,
            raw_sha256=version.raw_sha256,
        )
        self._ver_seq += 1
        self._memory_versions.setdefault(version.regulation_id, []).append(saved_v)
        return saved_v

    def list_unprocessed(self, limit: int = 10) -> list[LegalDocument]:
        return list(self._memory_docs.values())[:limit]

    def update_check_schedule(self, doc_id: int, next_check: datetime) -> None:
        if self.client:
            try:
                self.client.table("regulations").update(
                    {"next_check_at": next_check.isoformat()}
                ).eq("id", doc_id).execute()
            except Exception:
                pass


class SupabaseObligationRepository(ObligationRepository):
    """Repository managing compliance obligations."""

    def __init__(self, client: Any = None) -> None:
        self.client = client
        self._obligations: list[Obligation] = []
        self._seq = 1

    def save_obligations(self, obligations: list[Obligation]) -> list[Obligation]:
        saved: list[Obligation] = []
        for ob in obligations:
            if self.client:
                try:
                    data = {
                        "regulation_id": ob.regulation_id,
                        "version_id": ob.version_id,
                        "category": ob.category,
                        "applies_to": ob.applies_to,
                        "requirement_text": ob.requirement_text,
                        "evidence_quote": ob.evidence_quote,
                        "metric_name": ob.metric_name,
                        "operator": ob.operator,
                        "threshold_value": ob.threshold_value,
                        "unit": ob.unit,
                        "confidence": ob.confidence,
                        "model": ob.model,
                    }
                    res = self.client.table("obligations").insert(data).execute()
                    if res.data:
                        row = res.data[0]
                        saved.append(Obligation(
                            id=row["id"],
                            regulation_id=row["regulation_id"],
                            version_id=row.get("version_id"),
                            category=row["category"],
                            applies_to=row["applies_to"],
                            requirement_text=row["requirement_text"],
                            evidence_quote=row.get("evidence_quote", ""),
                            metric_name=row.get("metric_name"),
                            operator=row.get("operator"),
                            threshold_value=row.get("threshold_value"),
                            unit=row.get("unit"),
                        ))
                        continue
                except Exception:
                    pass

            item = Obligation(
                id=self._seq,
                regulation_id=ob.regulation_id,
                version_id=ob.version_id,
                category=ob.category,
                applies_to=ob.applies_to,
                requirement_text=ob.requirement_text,
                evidence_quote=ob.evidence_quote,
                metric_name=ob.metric_name,
                operator=ob.operator,
                threshold_value=ob.threshold_value,
                unit=ob.unit,
                confidence=ob.confidence,
            )
            self._seq += 1
            self._obligations.append(item)
            saved.append(item)
        return saved

    def get_by_regulation_version(self, version_id: int) -> list[Obligation]:
        return [o for o in self._obligations if o.version_id == version_id]

    def get_by_category(self, category: str) -> list[Obligation]:
        return [o for o in self._obligations if o.category == category]


class SupabasePolicyRepository(PolicyRepository):
    """Repository accessing internal company policies."""

    def __init__(self, client: Any = None) -> None:
        self.client = client
        self._policies: list[CompanyPolicy] = [
            CompanyPolicy(
                id=1,
                company_id=1,
                category="cyber_security",
                title="FinCorp Incident Reporting Policy",
                policy_text="All cyber incidents must be reported to the CERT team within 48 hours of detection.",
                metric_name="incident_report_hours",
                value=48.0,
                unit="hours",
            )
        ]

    def get_policies_for_company(self, company_id: int) -> list[CompanyPolicy]:
        if self.client:
            try:
                res = self.client.table("company_policies").select("*").eq("company_id", company_id).execute()
                if res.data:
                    return [
                        CompanyPolicy(
                            id=r["id"],
                            company_id=r["company_id"],
                            category=r.get("category", ""),
                            policy_text=r.get("policy_text", ""),
                            title=r.get("title", ""),
                            metric_name=r.get("metric_name"),
                            value=r.get("value"),
                            unit=r.get("unit"),
                        )
                        for r in res.data
                    ]
            except Exception:
                pass
        return [p for p in self._policies if p.company_id == company_id]

    def get_policies_by_category(self, company_id: int, category: str) -> list[CompanyPolicy]:
        all_policies = self.get_policies_for_company(company_id)
        # Soft match on category keywords
        return [p for p in all_policies if category in p.category or p.category in category]


class SupabaseCheckRepository(CheckRepository):
    """Repository recording compliance evaluations, risk scores, and alerts."""

    def __init__(self, client: Any = None) -> None:
        self.client = client
        self._checks: dict[str, ComplianceCheck] = {}
        self._risk_scores: list[RiskScore] = []
        self._alerts: list[Alert] = []
        self._seq = 1

    def get_check_by_inputs_hash(self, inputs_hash: str) -> ComplianceCheck | None:
        return self._checks.get(inputs_hash)

    def save_check(self, check: ComplianceCheck) -> ComplianceCheck:
        saved = ComplianceCheck(
            id=self._seq,
            obligation_id=check.obligation_id,
            company_policy_id=check.company_policy_id,
            company_id=check.company_id,
            verdict=check.verdict,
            confidence=check.confidence,
            explanation=check.explanation,
            method=check.method,
            inputs_hash=check.inputs_hash,
        )
        self._seq += 1
        if check.inputs_hash:
            self._checks[check.inputs_hash] = saved
        return saved

    def save_risk_score(self, risk_score: RiskScore) -> RiskScore:
        self._risk_scores.append(risk_score)
        return risk_score

    def save_alert(self, alert: Alert) -> Alert:
        self._alerts.append(alert)
        return alert
