from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_major_project_directories_exist():
    assert (ROOT / "backend").exists()
    assert (ROOT / "frontend").exists()
    assert (ROOT / "blockchain").exists()
    assert (ROOT / "ml").exists()


def test_report_assets_exist():
    assert (ROOT / "report-assets" / "report-tools.json").exists()
    assert (ROOT / "report-assets" / "testing-overview.md").exists()
    assert (ROOT / "report-assets" / "dashboard.css").exists()
    assert (ROOT / "report-assets" / "dashboard.js").exists()
    assert (ROOT / "report-dashboard.html").exists()
