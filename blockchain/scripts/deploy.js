const { ethers } = require("hardhat");

async function main() {
  console.log("🚀 Starting SALF Smart Contract Deployment...\n");

  const [deployer] = await ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log(
    "Account balance:",
    (await ethers.provider.getBalance(deployer.address)).toString(),
  );
  console.log("");

  // Deploy SALFAccessControl
  console.log("📝 Deploying SALFAccessControl...");
  const SALFAccessControl =
    await ethers.getContractFactory("SALFAccessControl");
  const accessControl = await SALFAccessControl.deploy();
  await accessControl.waitForDeployment();
  const accessControlAddress = await accessControl.getAddress();
  console.log("✅ SALFAccessControl deployed to:", accessControlAddress);

  // Deploy AcademicCreditLedger
  console.log("\n📝 Deploying AcademicCreditLedger...");
  const AcademicCreditLedger = await ethers.getContractFactory(
    "AcademicCreditLedger",
  );
  const creditLedger = await AcademicCreditLedger.deploy();
  await creditLedger.waitForDeployment();
  const creditLedgerAddress = await creditLedger.getAddress();
  console.log("✅ AcademicCreditLedger deployed to:", creditLedgerAddress);

  // Deploy ContributionRegistry
  console.log("\n📝 Deploying ContributionRegistry...");
  const ContributionRegistry = await ethers.getContractFactory(
    "ContributionRegistry",
  );
  const registry = await ContributionRegistry.deploy();
  await registry.waitForDeployment();
  const registryAddress = await registry.getAddress();
  console.log("✅ ContributionRegistry deployed to:", registryAddress);

  // Configure roles
  console.log("\n⚙️  Configuring roles...");

  // Grant validator role to credit ledger in access control
  const VALIDATOR_ROLE = ethers.keccak256(ethers.toUtf8Bytes("VALIDATOR_ROLE"));
  await accessControl.grantRole(VALIDATOR_ROLE, creditLedgerAddress);
  console.log("✅ Granted VALIDATOR_ROLE to AcademicCreditLedger");

  console.log("\n" + "=".repeat(60));
  console.log("🎉 DEPLOYMENT COMPLETE!");
  console.log("=".repeat(60));
  console.log("\nContract Addresses:");
  console.log("-".repeat(60));
  console.log(`SALFAccessControl:     ${accessControlAddress}`);
  console.log(`AcademicCreditLedger:  ${creditLedgerAddress}`);
  console.log(`ContributionRegistry:  ${registryAddress}`);
  console.log("-".repeat(60));
  console.log(
    "\n📋 Save these addresses in your .env file for backend configuration.",
  );

  // Return addresses for further use
  return {
    accessControl: accessControlAddress,
    creditLedger: creditLedgerAddress,
    registry: registryAddress,
  };
}

main()
  .then((addresses) => {
    console.log("\n✅ All contracts deployed successfully!");
    process.exit(0);
  })
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });
