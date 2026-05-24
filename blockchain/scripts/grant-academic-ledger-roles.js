/**
 * Grant FACULTY_ROLE, HOD_ROLE, REM_ROLE on an existing AcademicCreditLedger
 * to the backend operator wallet (same address as BESU_PRIVATE_KEY).
 *
 * Usage (run as the ledger deployer / admin):
 *   export ACADEMIC_CREDIT_ADDRESS=0x...
 *   export BESU_OPERATOR_ADDRESS=0x...   # optional; defaults to first signer
 *   npx hardhat run scripts/grant-academic-ledger-roles.js --network localhost
 */
const hre = require("hardhat");

async function main() {
  const ledgerAddr = process.env.ACADEMIC_CREDIT_ADDRESS;
  if (!ledgerAddr) {
    throw new Error("Set ACADEMIC_CREDIT_ADDRESS");
  }
  const [signer] = await hre.ethers.getSigners();
  const operator = process.env.BESU_OPERATOR_ADDRESS || signer.address;
  const ledger = await hre.ethers.getContractAt(
    "AcademicCreditLedger",
    ledgerAddr,
    signer,
  );
  const fr = await ledger.FACULTY_ROLE();
  const hr = await ledger.HOD_ROLE();
  const rr = await ledger.REM_ROLE();
  for (const [label, role] of [
    ["FACULTY_ROLE", fr],
    ["HOD_ROLE", hr],
    ["REM_ROLE", rr],
  ]) {
    const tx = await ledger.grantRole(role, operator);
    await tx.wait();
    console.log("Granted", label, "to", operator);
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
