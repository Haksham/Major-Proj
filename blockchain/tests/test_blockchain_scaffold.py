import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_JSON = ROOT / "blockchain" / "package.json"
CONTRACTS_DIR = ROOT / "blockchain" / "contracts"


def test_blockchain_package_exposes_test_script():
    package = json.loads(PACKAGE_JSON.read_text())

    assert package["name"] == "salf-blockchain"
    assert package["scripts"]["test"] == "hardhat test"


def test_core_contracts_exist():
    assert (CONTRACTS_DIR / "AcademicCreditLedger.sol").exists()
    assert (CONTRACTS_DIR / "ContributionRegistry.sol").exists()
    assert (CONTRACTS_DIR / "SALFAccessControl.sol").exists()
