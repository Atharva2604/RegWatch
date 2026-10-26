"""
Unit Tests for Loopholes 4 & 5:
- Multi-Tenancy JWT Authorization & Tenant Isolation
- Chief Compliance Officer (CCO) Override & Tamper-Evident Audit Defense
"""
import pytest
import jwt
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from api.main import app
from api.deps import (
    decode_supabase_jwt,
    verify_tenant_access,
    require_role,
    AuthUser,
)

client = TestClient(app)


def test_decode_supabase_jwt_valid():
    payload = {
        "sub": "11111111-2222-3333-4444-555555555555",
        "email": "cco@fincorp.example.com",
        "role": "authenticated",
        "app_metadata": {"company_id": 10, "role": "officer"},
    }
    token = jwt.encode(payload, "secret-key", algorithm="HS256")

    decoded = decode_supabase_jwt(token)
    assert decoded["sub"] == "11111111-2222-3333-4444-555555555555"
    assert decoded["email"] == "cco@fincorp.example.com"


def test_verify_tenant_access_permits_same_company():
    user = AuthUser(user_id="u1", company_id=10, role="viewer")
    verified_id = verify_tenant_access(user, requested_company_id=10)
    assert verified_id == 10


def test_verify_tenant_access_rejects_cross_tenant_access():
    user = AuthUser(user_id="u1", company_id=10, role="officer")
    # Officer of company 10 attempting to access company 6 (PayFast Payments)
    with pytest.raises(HTTPException) as exc_info:
        verify_tenant_access(user, requested_company_id=6)

    assert exc_info.value.status_code == 403
    assert "Cross-tenant access forbidden" in exc_info.value.detail


def test_verify_tenant_access_allows_admin():
    admin_user = AuthUser(user_id="admin-1", company_id=10, role="admin")
    # Admin can access another company for regulatory supervision
    verified_id = verify_tenant_access(admin_user, requested_company_id=6)
    assert verified_id == 10


def test_require_role_rejects_viewer_for_officer_action():
    viewer = AuthUser(user_id="v1", company_id=10, role="viewer")
    role_checker = require_role(["officer", "admin"])

    with pytest.raises(HTTPException) as exc_info:
        role_checker(auth_user=viewer)

    assert exc_info.value.status_code == 403
    assert "Permission denied" in exc_info.value.detail


def test_cco_override_endpoint_requires_legal_opinion():
    # Attempt override with empty legal opinion
    response = client.post(
        "/v1/alerts/syn-123/override",
        json={"legal_opinion": "  ", "board_resolution_number": "BR-1"},
    )
    # Should reject due to insufficient opinion text (< 10 chars)
    assert response.status_code == 422


def test_cco_override_endpoint_records_tamper_proof_audit():
    override_body = {
        "legal_opinion": "Formal legal opinion received from Senior Counsel confirming client consent safeguards satisfy SEBI mandate under compensatory Board policies.",
        "board_resolution_number": "BR-2026/04-A",
        "signer_name": "Chief Compliance Officer",
    }

    response = client.post("/v1/alerts/syn-9999/override", json=override_body)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "exempted"
    assert data["verdict"] == "exempted"
    assert data["board_resolution_number"] == "BR-2026/04-A"
    assert "audit_defense_signature" in data
    assert len(data["audit_defense_signature"]) == 64  # SHA-256 hex digest
