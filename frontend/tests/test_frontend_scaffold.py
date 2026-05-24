from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
API_FILE = ROOT / "frontend" / "src" / "services" / "api.js"
STORE_FILE = ROOT / "frontend" / "src" / "store" / "index.js"


def test_api_service_contains_core_endpoint_groups():
    source = API_FILE.read_text()

    assert "export const authAPI" in source
    assert "export const contributionsAPI" in source
    assert 'api.post("/auth/login"' in source
    assert 'api.get("/portfolio/me")' in source


def test_auth_store_persists_session_state():
    source = STORE_FILE.read_text()

    assert 'name: "salf-auth-storage"' in source
    assert "needsRegistration" in source
    assert "pendingApproval" in source
    assert "logout: () =>" in source
