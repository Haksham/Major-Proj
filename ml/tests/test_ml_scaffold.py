from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ML_SERVICE_FILE = ROOT / "ml" / "ml_service.py"
GATEKEEPER_FILE = ROOT / "ml" / "gatekeeper.py"


def test_ml_service_declares_core_benchmark_categories():
    source = ML_SERVICE_FILE.read_text()

    assert "BENCHMARK_ATTRIBUTES" in source
    assert '"research_quality"' in source
    assert '"academic_impact"' in source
    assert '@app.post("/evaluate"' in source
    assert '@app.get("/health")' in source


def test_gatekeeper_service_mentions_duplicate_and_anomaly_checks():
    source = GATEKEEPER_FILE.read_text()

    assert "check_duplicate" in source
    assert "check_ai_text" in source
    assert "check_anomaly" in source
    assert "evaluate" in source
