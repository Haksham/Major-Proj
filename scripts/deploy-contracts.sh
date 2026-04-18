#!/bin/bash
# SALF - Smart Contract Deployment Script
# Deploys all smart contracts to Hyperledger Besu network

set -e

echo "========================================="
echo "SALF Smart Contract Deployment"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "blockchain/hardhat.config.js" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Navigate to blockchain directory
cd blockchain

# Check for node_modules
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Compile contracts
echo -e "${YELLOW}Compiling smart contracts...${NC}"
npx hardhat compile

# Check compilation success
if [ $? -ne 0 ]; then
    echo -e "${RED}Compilation failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Compilation successful!${NC}"

# Deploy contracts
NETWORK=${1:-localhost}
echo -e "${YELLOW}Deploying to network: ${NETWORK}${NC}"

# Run deployment
npx hardhat run scripts/deploy.js --network $NETWORK

if [ $? -eq 0 ]; then
    echo -e "${GREEN}=========================================${NC}"
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "${GREEN}=========================================${NC}"
    
    # Check if deployment output exists
    if [ -f "deployments/localhost.json" ]; then
        echo ""
        echo "Contract Addresses:"
        cat deployments/localhost.json
    fi
else
    echo -e "${RED}Deployment failed!${NC}"
    exit 1
fi

cd ..
echo ""
echo "Next steps:"
echo "1. Update .env files with contract addresses"
echo "2. Start the backend and frontend services"
echo "3. Connect MetaMask to Besu network (RPC: http://localhost:8545)"
