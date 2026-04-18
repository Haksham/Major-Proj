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

Add the SALF network to MetaMask:

- **Network Name**: SALF Besu Network
- **RPC URL**: http://localhost:8545
- **Chain ID**: 1337
- **Currency Symbol**: ETH

Import test account (development only):

- **Private Key**: `0x8f2a55949038a9610f50fb23b5883af3b4ecb3c3bb792cbcefbd1542c692be63`

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

| Activity Type                  | Base Points |
| ------------------------------ | ----------- |
| Refereed Journal Publication   | 25          |
| International Authored Book    | 30          |
| National Authored Book         | 20          |
| Patent (Granted)               | 50          |
| Patent (Filed)                 | 25          |
| International Conference Paper | 15          |
| National Conference Paper      | 10          |
| Major Research Project         | 40          |
| Minor Research Project         | 20          |
| Consultancy                    | 30          |

### Credit Formula

```
Final Credits = Base Points × (1 + Quality Score/100) × (1 + Novelty Multiplier)
```

Where:

- **Quality Score**: AI-evaluated score (0-100) based on 36 benchmark attributes
- **Novelty Multiplier**: Originality factor (0.0-0.5)

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
