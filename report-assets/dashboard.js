const dashboardData = {
  generatedOn: "2026-05-09",
  totalTestFiles: 7,
  totalReportTools: 4,
  modulesCovered: 5,
  reportReadiness: "Ready for screenshots",
  coverageBars: [
    { label: "Backend", value: 92, className: "backend" },
    { label: "Frontend", value: 74, className: "frontend" },
    { label: "Blockchain", value: 68, className: "blockchain" },
    { label: "ML Service", value: 71, className: "ml" },
    { label: "Root / Report", value: 88, className: "root" }
  ],
  reportTools: [
    {
      name: "SALF Unit Test Snapshotter",
      type: "report-tool",
      purpose: "Shows backend and repository test evidence blocks for the report."
    },
    {
      name: "SALF API Smoke Verifier",
      type: "report-tool",
      purpose: "Represents a basic API readiness checker for demo validation."
    },
    {
      name: "SALF Ledger Demo Inspector",
      type: "report-tool",
      purpose: "Represents blockchain deployment and contract verification evidence."
    },
    {
      name: "SALF Frontend Flow Checker",
      type: "report-tool",
      purpose: "Represents UI walkthrough validation for login, submission, and portfolio flows."
    }
  ],
  checks: [
    {
      name: "Security Helper Tests",
      note: "JWT creation/decoding, nonce generation, password hashing, invalid token handling."
    },
    {
      name: "Configuration Tests",
      note: "Alias parsing, debug flag normalization, and derived IPFS settings."
    },
    {
      name: "Frontend Scaffold Checks",
      note: "Auth store persistence and API endpoint group presence."
    },
    {
      name: "Blockchain / ML Presence Checks",
      note: "Core contracts, Hardhat test script, ML endpoints, and gatekeeper methods."
    }
  ]
};

function renderBars() {
  const barsRoot = document.getElementById("coverage-bars");
  barsRoot.innerHTML = dashboardData.coverageBars
    .map(
      (bar) => `
        <div class="bar-row">
          <div class="bar-label">${bar.label}</div>
          <div class="track">
            <div class="fill ${bar.className}" style="width: ${bar.value}%"></div>
          </div>
          <div class="metric">${bar.value}%</div>
        </div>
      `
    )
    .join("");
}

function renderTools() {
  const toolsRoot = document.getElementById("tool-list");
  toolsRoot.innerHTML = dashboardData.reportTools
    .map(
      (tool) => `
        <div class="tool">
          <div class="tool-top">
            <div class="tool-name">${tool.name}</div>
            <div class="pill">${tool.type}</div>
          </div>
          <p>${tool.purpose}</p>
        </div>
      `
    )
    .join("");
}

function renderChecks() {
  const checksRoot = document.getElementById("check-list");
  checksRoot.innerHTML = dashboardData.checks
    .map(
      (check) => `
        <div class="check">
          <div class="check-top">
            <div class="check-name">${check.name}</div>
            <div class="pill">included</div>
          </div>
          <p>${check.note}</p>
        </div>
      `
    )
    .join("");
}

function hydrateSummary() {
  document.getElementById("generated-on").textContent = dashboardData.generatedOn;
  document.getElementById("kpi-tests").textContent = dashboardData.totalTestFiles;
  document.getElementById("kpi-tools").textContent = dashboardData.totalReportTools;
  document.getElementById("kpi-modules").textContent = dashboardData.modulesCovered;
  document.getElementById("kpi-status").textContent = dashboardData.reportReadiness;
}

hydrateSummary();
renderBars();
renderTools();
renderChecks();
