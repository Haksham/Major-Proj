import { ethers } from "ethers";

// Contract ABIs (simplified for frontend interaction)
const ACCESS_CONTROL_ABI = [
  "function hasRole(bytes32 role, address account) view returns (bool)",
  "function FACULTY_ROLE() view returns (bytes32)",
  "function HOD_ROLE() view returns (bytes32)",
  "function ADMIN_ROLE() view returns (bytes32)",
  "function getFacultyInfo(address faculty) view returns (tuple(string name, string department, string employeeId, uint256 registrationDate, bool isActive))",
  "function registerFaculty(address faculty, string name, string department, string employeeId)",
  "event FacultyRegistered(address indexed faculty, string name, string department)",
];

const ACADEMIC_LEDGER_ABI = [
  "function submitRecord(uint8 category, string title, string ipfsHash, string description) returns (uint256)",
  "function getContribution(uint256 contributionId) view returns (tuple(address faculty, uint8 category, string title, string ipfsHash, string description, uint256 timestamp, uint8 status, uint256 qualityScore, uint256 noveltyScore, uint256 finalCredits, address evaluatedBy))",
  "function getFacultyContributions(address faculty) view returns (uint256[])",
  "function recordEvaluation(uint256 contributionId, uint256 qualityScore, uint256 noveltyScore)",
  "function validateBlock(uint256 contributionId)",
  "function rejectContribution(uint256 contributionId, string reason)",
  "function getFacultyTotalCredits(address faculty) view returns (uint256)",
  "function getTotalContributions() view returns (uint256)",
  "event RecordSubmitted(uint256 indexed contributionId, address indexed faculty, uint8 category, string title)",
  "event RecordEvaluated(uint256 indexed contributionId, uint256 qualityScore, uint256 noveltyScore, uint256 credits)",
  "event BlockValidated(uint256 indexed contributionId, address indexed validator)",
];

const CONTRIBUTION_REGISTRY_ABI = [
  "function getRegisteredInstitutions() view returns (address[])",
  "function requestTransfer(address toInstitution, uint256 contributionId)",
  "function approveTransfer(uint256 transferId)",
  "event TransferRequested(uint256 indexed transferId, address indexed from, address indexed to, uint256 contributionId)",
  "event TransferApproved(uint256 indexed transferId)",
];

// Contract addresses (to be updated after deployment)
const CONTRACT_ADDRESSES = {
  accessControl:
    import.meta.env.VITE_ACCESS_CONTROL_ADDRESS ||
    "0x0000000000000000000000000000000000000000",
  academicLedger:
    import.meta.env.VITE_ACADEMIC_LEDGER_ADDRESS ||
    "0x0000000000000000000000000000000000000000",
  contributionRegistry:
    import.meta.env.VITE_CONTRIBUTION_REGISTRY_ADDRESS ||
    "0x0000000000000000000000000000000000000000",
};

// Network configuration
const NETWORK_CONFIG = {
  chainId: import.meta.env.VITE_CHAIN_ID || "0x539", // 1337 in hex
  chainName: "SALF Private Network",
  rpcUrls: [import.meta.env.VITE_RPC_URL || "http://localhost:8545"],
  nativeCurrency: {
    name: "Ether",
    symbol: "ETH",
    decimals: 18,
  },
};

/**
 * Web3 Service for blockchain interactions
 */
class Web3Service {
  constructor() {
    this.provider = null;
    this.signer = null;
    this.contracts = {};
  }

  /**
   * Initialize the Web3 connection
   */
  async initialize() {
    if (typeof window.ethereum === "undefined") {
      throw new Error("MetaMask is not installed");
    }

    this.provider = new ethers.BrowserProvider(window.ethereum);

    // Setup event listeners
    window.ethereum.on("chainChanged", () => window.location.reload());
    window.ethereum.on("accountsChanged", (accounts) => {
      if (accounts.length === 0) {
        console.log("Please connect to MetaMask");
      }
    });
  }

  /**
   * Connect wallet and get signer
   */
  async connectWallet() {
    if (!this.provider) {
      await this.initialize();
    }

    // Request account access
    const accounts = await this.provider.send("eth_requestAccounts", []);

    if (accounts.length === 0) {
      throw new Error("No accounts found");
    }

    // Check and switch network if needed
    await this.switchNetwork();

    this.signer = await this.provider.getSigner();

    // Initialize contracts
    await this.initializeContracts();

    return accounts[0];
  }

  /**
   * Switch to SALF network
   */
  async switchNetwork() {
    try {
      await window.ethereum.request({
        method: "wallet_switchEthereumChain",
        params: [{ chainId: NETWORK_CONFIG.chainId }],
      });
    } catch (switchError) {
      // If chain doesn't exist, add it
      if (switchError.code === 4902) {
        await window.ethereum.request({
          method: "wallet_addEthereumChain",
          params: [NETWORK_CONFIG],
        });
      } else {
        throw switchError;
      }
    }
  }

  /**
   * Initialize smart contracts
   */
  async initializeContracts() {
    if (!this.signer) {
      throw new Error("Wallet not connected");
    }

    this.contracts = {
      accessControl: new ethers.Contract(
        CONTRACT_ADDRESSES.accessControl,
        ACCESS_CONTROL_ABI,
        this.signer,
      ),
      academicLedger: new ethers.Contract(
        CONTRACT_ADDRESSES.academicLedger,
        ACADEMIC_LEDGER_ABI,
        this.signer,
      ),
      contributionRegistry: new ethers.Contract(
        CONTRACT_ADDRESSES.contributionRegistry,
        CONTRIBUTION_REGISTRY_ABI,
        this.signer,
      ),
    };
  }

  /**
   * Sign message for authentication
   */
  async signMessage(message) {
    if (!this.signer) {
      throw new Error("Wallet not connected");
    }

    return await this.signer.signMessage(message);
  }

  /**
   * Get connected wallet address
   */
  async getAddress() {
    if (!this.signer) {
      throw new Error("Wallet not connected");
    }

    return await this.signer.getAddress();
  }

  /**
   * Check user role
   */
  async getUserRole(address) {
    if (!this.contracts.accessControl) {
      throw new Error("Contracts not initialized");
    }

    const [isFaculty, isHoD, isAdmin] = await Promise.all([
      this.contracts.accessControl.hasRole(
        await this.contracts.accessControl.FACULTY_ROLE(),
        address,
      ),
      this.contracts.accessControl.hasRole(
        await this.contracts.accessControl.HOD_ROLE(),
        address,
      ),
      this.contracts.accessControl.hasRole(
        await this.contracts.accessControl.ADMIN_ROLE(),
        address,
      ),
    ]);

    if (isAdmin) return "admin";
    if (isHoD) return "hod";
    if (isFaculty) return "faculty";
    return "unregistered";
  }

  /**
   * Get faculty information
   */
  async getFacultyInfo(address) {
    if (!this.contracts.accessControl) {
      throw new Error("Contracts not initialized");
    }

    const info = await this.contracts.accessControl.getFacultyInfo(address);
    return {
      name: info.name,
      department: info.department,
      employeeId: info.employeeId,
      registrationDate: new Date(Number(info.registrationDate) * 1000),
      isActive: info.isActive,
    };
  }

  /**
   * Submit a contribution record
   */
  async submitContribution(category, title, ipfsHash, description) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const tx = await this.contracts.academicLedger.submitRecord(
      category,
      title,
      ipfsHash,
      description,
    );

    const receipt = await tx.wait();

    // Find the RecordSubmitted event
    const event = receipt.logs.find(
      (log) => log.fragment?.name === "RecordSubmitted",
    );

    return {
      transactionHash: receipt.hash,
      contributionId: event ? Number(event.args[0]) : null,
      blockNumber: receipt.blockNumber,
    };
  }

  /**
   * Get contribution details
   */
  async getContribution(contributionId) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const contribution =
      await this.contracts.academicLedger.getContribution(contributionId);

    return {
      faculty: contribution.faculty,
      category: Number(contribution.category),
      title: contribution.title,
      ipfsHash: contribution.ipfsHash,
      description: contribution.description,
      timestamp: new Date(Number(contribution.timestamp) * 1000),
      status: Number(contribution.status),
      qualityScore: Number(contribution.qualityScore),
      noveltyScore: Number(contribution.noveltyScore),
      finalCredits: Number(contribution.finalCredits),
      evaluatedBy: contribution.evaluatedBy,
    };
  }

  /**
   * Get faculty's total credits
   */
  async getFacultyCredits(address) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const credits =
      await this.contracts.academicLedger.getFacultyTotalCredits(address);
    return Number(credits);
  }

  /**
   * Get faculty's contribution IDs
   */
  async getFacultyContributions(address) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const ids =
      await this.contracts.academicLedger.getFacultyContributions(address);
    return ids.map((id) => Number(id));
  }

  /**
   * Evaluate a contribution (HoD/Admin)
   */
  async evaluateContribution(contributionId, qualityScore, noveltyScore) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const tx = await this.contracts.academicLedger.recordEvaluation(
      contributionId,
      qualityScore,
      noveltyScore,
    );

    return await tx.wait();
  }

  /**
   * Validate a contribution block (HoD)
   */
  async validateContribution(contributionId) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const tx =
      await this.contracts.academicLedger.validateBlock(contributionId);
    return await tx.wait();
  }

  /**
   * Reject a contribution (HoD)
   */
  async rejectContribution(contributionId, reason) {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const tx = await this.contracts.academicLedger.rejectContribution(
      contributionId,
      reason,
    );
    return await tx.wait();
  }

  /**
   * Request credit transfer to another institution
   */
  async requestTransfer(toInstitution, contributionId) {
    if (!this.contracts.contributionRegistry) {
      throw new Error("Contracts not initialized");
    }

    const tx = await this.contracts.contributionRegistry.requestTransfer(
      toInstitution,
      contributionId,
    );
    return await tx.wait();
  }

  /**
   * Get total contributions count
   */
  async getTotalContributions() {
    if (!this.contracts.academicLedger) {
      throw new Error("Contracts not initialized");
    }

    const total = await this.contracts.academicLedger.getTotalContributions();
    return Number(total);
  }

  /**
   * Disconnect wallet
   */
  disconnect() {
    this.signer = null;
    this.contracts = {};
  }
}

// Singleton instance
export const web3Service = new Web3Service();

// Category mappings
export const CONTRIBUTION_CATEGORIES = {
  0: "Guest Lectures",
  1: "Journal Publication",
  2: "Book",
  3: "Book Chapter",
  4: "Patent",
  5: "Conference",
  6: "Workshop",
  7: "Seminar",
  8: "Project",
  9: "Award",
  10: "Faculty Development Program",
};

export const CONTRIBUTION_STATUS = {
  0: "Pending",
  1: "Under Review",
  2: "Approved",
  3: "Rejected",
  4: "Validated",
};

export const UGC_BASE_POINTS = {
  0: 25, // Guest Lectures
  1: 25, // Journal Publication
  2: 30, // Book (International)
  3: 10, // Book Chapter
  4: 50, // Patent
  5: 10, // Conference (International)
  6: 5, // Workshop
  7: 5, // Seminar
  8: 20, // Project
  9: 15, // Award
  10: 0, // Faculty Development Program
};

export default web3Service;
