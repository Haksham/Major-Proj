import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "report-assets" / "report-tools.json"


def test_tools_manifest_has_multiple_entries():
    data = json.loads(MANIFEST.read_text())

    assert "tools" in data
    assert len(data["tools"]) >= 3


def test_tools_manifest_entries_have_report_fields():
    data = json.loads(MANIFEST.read_text())

    for tool in data["tools"]:
        assert tool["name"]
        assert tool["type"]
        assert tool["purpose"]
        assert tool["report_label"]
