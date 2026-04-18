#!/bin/bash
# SALF Development Environment Setup Script
# Sets up the complete development environment

set -e

echo "========================================="
echo "SALF Development Environment Setup"
echo "========================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists node; then
    echo -e "${RED}Node.js is not installed. Please install Node.js 18+${NC}"
    exit 1
fi

if ! command_exists python3; then
    echo -e "${RED}Python3 is not installed. Please install Python 3.10+${NC}"
    exit 1
fi

if ! command_exists docker; then
    echo -e "${YELLOW}Docker is not installed. Docker is required for full deployment.${NC}"
fi

echo -e "${GREEN}Prerequisites check passed!${NC}"

# Create directories
echo -e "${BLUE}Creating required directories...${NC}"
mkdir -p blockchain/deployments
mkdir -p backend/logs
mkdir -p docker/data/besu
mkdir -p docker/data/ipfs
mkdir -p docker/data/postgres

# Setup blockchain
echo -e "${YELLOW}Setting up blockchain environment...${NC}"
cd blockchain
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# Setup backend
echo -e "${YELLOW}Setting up backend environment...${NC}"
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Setup frontend
echo -e "${YELLOW}Setting up frontend environment...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
fi
cd ..

# Setup ML service
echo -e "${YELLOW}Setting up ML service...${NC}"
cd ml
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# Create .env files if they don't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating root .env file...${NC}"
    cat > .env << EOF
# SALF Environment Configuration

# Network
BESU_RPC_URL=http://localhost:8545
BESU_WS_URL=ws://localhost:8546

# Database
POSTGRES_USER=salf_user
POSTGRES_PASSWORD=secure_password_change_me
POSTGRES_DB=salf_db
DATABASE_URL=postgresql://salf_user:secure_password_change_me@localhost:5432/salf_db

# Redis
REDIS_URL=redis://localhost:6379

# IPFS
IPFS_API_URL=http://localhost:5001
IPFS_GATEWAY_URL=http://localhost:8080

# JWT
JWT_SECRET=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ML Service
ML_SERVICE_URL=http://localhost:8001

# Contract Addresses (update after deployment)
ACCESS_CONTROL_CONTRACT=0x...
ACADEMIC_LEDGER_CONTRACT=0x...
CONTRIBUTION_REGISTRY_CONTRACT=0x...
EOF
fi

if [ ! -f "backend/.env" ]; then
    cp .env backend/.env
    echo -e "${GREEN}Created backend/.env${NC}"
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "1. Update .env files with your configuration"
echo "2. Start infrastructure services:"
echo "   docker-compose -f docker/docker-compose.yml up -d besu-node1 ipfs postgres redis"
echo "3. Deploy smart contracts:"
echo "   ./scripts/deploy-contracts.sh"
echo "4. Start backend (in new terminal):"
echo "   cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "5. Start frontend (in new terminal):"
echo "   cd frontend && npm run dev"
echo "6. Start ML service (in new terminal):"
echo "   cd ml && source venv/bin/activate && uvicorn ml_service:app --port 8001"
echo ""
echo "Or use Docker for full deployment:"
echo "   docker-compose -f docker/docker-compose.yml up --build"
