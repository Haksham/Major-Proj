# Blockchain-Backed Faculty Contribution and Academic Credit Ledger (SALF)

## Secure Academic Ledger Framework

A decentralized web-based application designed to modernize the evaluation of academic faculty by transitioning from manual, subjective reviews to a model of "algorithmic trust".

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Frontend (React)                                │
│                    Web Dashboard + MetaMask Integration                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API Gateway (FastAPI)                              │
│              ┌──────────────────┬──────────────────┐                        │
│              │  ML Gatekeeper   │  REST Endpoints  │                        │
│              │  (Fraud Det.)    │                  │                        │
│              └──────────────────┴──────────────────┘                        │
└─────────────────────────────────────────────────────────────────────────────┘
         │                    │                         │
         ▼                    ▼                         ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────────┐
│   IPFS Storage  │  │  REM (AI/NLP)   │  │    Hyperledger Besu Network    │
│   (Documents)   │  │  Sentence-BERT  │  │         IBFT 2.0 PoA           │
└─────────────────┘  └─────────────────┘  │  ┌─────────────────────────┐   │
                                          │  │    Smart Contracts      │   │
                                          │  │  - AcademicCredits.sol  │   │
                                          │  │  - AccessControl.sol    │   │
                                          │  │  - ContributionLedger   │   │
                                          │  └─────────────────────────┘   │
                                          └─────────────────────────────────┘
```

## Features

- **User Authentication & RBAC**: Secure login via MetaMask wallet with role-based access
- **Decentralized Record Submission**: IPFS storage for documents, blockchain for metadata
- **AI-Driven Automated Scoring (REM)**: NLP analysis of research abstracts using Sentence-BERT
- **UGC Credit Mapping**: Automatic point allocation based on statutory tables
- **Fraud Detection**: ML-based gatekeeper for anomaly detection
- **Academic Credit Portfolio**: Real-time dashboard for tracking verified contributions
- **IBFT 2.0 Consensus**: Proof of Authority for immediate finality

## Project Structure

```
block_lkedger/
├── blockchain/           # Hyperledger Besu configuration & smart contracts
│   ├── config/          # Network configuration files
│   ├── contracts/       # Solidity smart contracts
│   └── scripts/         # Deployment scripts
├── backend/             # FastAPI backend application
│   ├── app/
│   │   ├── api/        # REST API endpoints
│   │   ├── core/       # Core configuration
│   │   ├── models/     # Database models
│   │   ├── schemas/    # Pydantic schemas
│   │   └── services/   # Business logic services
│   └── tests/          # Backend tests
├── frontend/            # React frontend application
│   ├── src/
│   │   ├── components/ # React components
│   │   ├── pages/      # Page components
│   │   ├── services/   # API services
│   │   └── utils/      # Utility functions
│   └── public/
├── ml/                  # Machine Learning models
│   ├── models/         # Trained models
│   └── data/           # Training data
├── ipfs/               # IPFS configuration
├── docker/             # Docker configurations
├── scripts/            # Utility scripts
└── docs/               # Documentation
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- MetaMask browser extension

## Quick Start

### Option 1: Docker Deployment (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd block_lkedger

# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings

# Start all services
cd docker
docker-compose up --build -d

# View logs
docker-compose logs -f
```

Services will be available at:

- **Frontend**: http://localhost:80
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **IPFS Gateway**: http://localhost:8080

### Option 2: Development Setup

```bash
# Run setup script
chmod +x scripts/setup-dev.sh
./scripts/setup-dev.sh
```

Or manually:

#### 1. Setup Environment

```bash
cp .env.example .env
cp .env backend/.env
```

#### 2. Start Infrastructure

```bash
cd docker
docker-compose up -d besu-node1 besu-node2 ipfs postgres redis
```

#### 3. Deploy Smart Contracts

```bash
cd blockchain
npm install
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
# Note: Update .env with deployed contract addresses (in backend folder)
```

#### 4. Start Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 5. Start ML Service

```bash
cd ml
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn ml_service:app --port 8001
```

#### 6. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### MetaMask Configuration

Add the SALF local network to MetaMask:

| Field           | Value                        |
| --------------- | ---------------------------- |
| Network Name    | SALF Besu Local              |
| RPC URL         | http://localhost:8545         |
| Chain ID        | **31337**                    |
| Currency Symbol | ETH                          |

> **Note:** Chain ID is `31337` (Hardhat/Anvil default). Do not use `1337`.

#### Deployed Contracts (local Hardhat node)

| Contract                 | Address                                      |
| ------------------------ | -------------------------------------------- |
| `SALFAccessControl`      | `0x2279B7A0a67DB372996a5FaB50D91eAA73d2eBe6` |
| `AcademicCreditLedger`   | `0x8A791620dd6260079BF849Dc5567aDC3F2FdC318` |
| `ContributionRegistry`   | `0x610178dA211FEF7D417bC0e6FeD39F05609AD788` |

> Contracts must be redeployed after every Hardhat node restart:
> ```bash
> npx hardhat run scripts/deploy.js --network localhost
> ```

#### Seeded Accounts (development)

| Role            | Name                | Wallet Address                               |
| --------------- | ------------------- | -------------------------------------------- |
| Master Admin    | Admin User          | `0x3Ad3616fe1E978a3FcB1AC52806652C0254d00BA` |
| Institute Admin | Dr. Suresh Kumar    | `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` |
| HoD (CSE)       | Dr. Rajesh Nair     | `0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC` |
| Faculty         | Dr. Priya Sharma    | `0x90F79bf6EB2c4f870365E785982E1f101E93b906` |
| Faculty         | Dr. Vikram Rao      | `0x15d34AAf54267Db7D7c367839AAf71A00a2C6A65` |
| Faculty         | Dr. Anitha Krishnan | `0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc` |

## Testing

### Smart Contract Tests

```bash
cd blockchain
npx hardhat test
```

### Backend Tests

```bash
cd backend
source venv/bin/activate
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## UGC Credit Mapping Table

Base points are defined in `backend/app/core/config.py` and applied automatically when a faculty member submits a contribution.

| Activity Type                  | Base Points |
| ------------------------------ | ----------- |
| Refereed Journal Publication   | 25          |
| International Authored Book    | 30          |
| National Authored Book         | 20          |
| Book Chapter                   | 5           |
| International Conference Paper | 10          |
| National Conference Paper      | 10          |
| Patent (Filed)                 | 15          |
| Patent (Granted)               | 30          |
| Editorial Work                 | 10          |
| Research Project               | 20          |

### Credit Formula

```
Final Credits = Base Points × (1 + Quality Score / 100) × (1 + Novelty Percentage / 200)
```

Where:

- **Base Points**: UGC-defined points per contribution category (table above)
- **Quality Score**: AI-evaluated score (0–100) from the REM service using Sentence-BERT across 36 benchmark attributes
- **Novelty Percentage**: Originality score (0–100) from embedding variance and innovation keyword density

**Example:** A Refereed Journal (base = 25) with quality score 84 and novelty 62%:
```
Final = 25 × (1 + 84/100) × (1 + 62/200) = 25 × 1.84 × 1.31 ≈ 60.2 credits
```

## Blockchain Ledger — How It Works

Every action in SALF is recorded as an **immutable on-chain transaction** on a private Hyperledger Besu network running IBFT 2.0 Proof-of-Authority consensus.

### What Each Block Represents

Unlike Ethereum mainnet (where blocks are mined on a timer), **Hardhat mines one block per transaction**. Each block number therefore directly maps to an on-chain event:

| Transaction Type       | Smart Contract Function          | Who Triggers       |
| ---------------------- | -------------------------------- | ------------------ |
| Contract deployment    | `constructor()`                  | Deployer           |
| Faculty submission     | `submitRecord()`                 | Faculty member     |
| AI evaluation          | `recordEvaluation()`             | REM service        |
| HoD validates          | `validateBlock()`                | Head of Department |
| HoD rejects            | `rejectContribution()`           | Head of Department |
| Fraud flag             | `flagContribution()`             | HoD / System       |
| Role assignment        | `grantRole()`                    | Admin              |

**Example — Block #29** in a live session:
```
eth_sendRawTransaction
  Contract call:    AcademicCreditLedger#validateBlock
  From:             0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266
  To:               0x8A791620dd6260079BF849Dc5567aDC3F2FdC318
  Value:            0 ETH
  Gas used:         227592
```

This means contribution #4 was permanently validated and its final credits written to the blockchain at block 29 — tamper-proof and auditable by any node on the network.

### Admin Dashboard — Live Chain Stats

The Master Admin overview displays a **live blockchain banner** that auto-refreshes every 5 seconds:

| Metric            | Description                                               |
| ----------------- | --------------------------------------------------------- |
| Blocks Mined      | Total on-chain transactions since node start              |
| On-Chain Records  | Contribution + user records written to the ledger         |
| Credits On-Chain  | Sum of all validated faculty credits across all faculties |
| Chain ID          | `31337` — IBFT 2.0 PoA private network identifier         |

A green pulsing dot indicates live connectivity to the Besu node.

## Smart Contracts

| Contract                 | Description                                 |
| ------------------------ | ------------------------------------------- |
| SALFAccessControl.sol    | RBAC for Faculty, HoD, Admin roles          |
| AcademicCreditLedger.sol | Main contract for contributions and credits |
| ContributionRegistry.sol | Inter-institutional credit portability      |

## Documentation

- [API Documentation](docs/API.md)
- [User Manual](docs/USER_MANUAL.md)
- [Smart Contract Docs](blockchain/contracts/)

## API Documentation

Once the backend is running, access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security Features

- **SHA-256** hashing for data integrity
- **RSA** digital signatures for transactions
- **AES-256** encryption for sensitive data
- **MetaMask** for secure key management
- **IBFT 2.0 PoA** consensus for network security

## Performance Targets

- Throughput: >30 TPS
- P95 Latency: <300ms
- Memory footprint: ~45-52 MB for access control layer

## Tech Stack

| Layer             | Technology                       |
| ----------------- | -------------------------------- |
| Blockchain        | Hyperledger Besu (IBFT 2.0 PoA)  |
| Smart Contracts   | Solidity 0.8.20, OpenZeppelin v5 |
| Backend           | FastAPI (Python 3.11), Web3.py   |
| Frontend          | React 18, Vite, Tailwind CSS     |
| State Management  | Zustand                          |
| Blockchain Client | ethers.js v6                     |
| AI/ML             | Sentence-BERT (all-MiniLM-L6-v2) |
| Storage           | IPFS (Kubo), PostgreSQL          |
| Cache             | Redis                            |
| Containerization  | Docker, docker-compose           |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- University Grants Commission (UGC) for credit mapping guidelines
- Hyperledger Foundation for Besu
- Sentence-Transformers team for NLP models
