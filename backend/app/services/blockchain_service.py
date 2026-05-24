"""
SALF Blockchain Service
Web3 integration for Hyperledger Besu interaction
"""
import json
import os
import secrets
from typing import Optional, Dict, Any, List
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from eth_account import Account
from pathlib import Path

from app.core.config import settings


class BlockchainService:
    """Service for interacting with Hyperledger Besu blockchain."""
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(settings.BESU_RPC_URL))
        # Inject PoA middleware for IBFT 2.0
        self.w3.middleware_onion.add(ExtraDataToPOAMiddleware, "poa")
        
        # Load contract ABIs
        self.contracts = {}
        self._load_contracts()
        
        # Set default account if private key is provided
        if settings.BESU_PRIVATE_KEY:
            self.account = Account.from_key(settings.BESU_PRIVATE_KEY)
        else:
            self.account = None
    
    def _load_contracts(self):
        """Load contract ABIs from compiled artifacts."""
        artifacts_path = Path(__file__).parent.parent.parent.parent / "blockchain" / "artifacts" / "contracts"
        
        contract_configs = {
            "access_control": {
                "abi_path": artifacts_path / "SALFAccessControl.sol" / "SALFAccessControl.json",
                "address": settings.ACCESS_CONTROL_ADDRESS
            },
            "academic_credit": {
                "abi_path": artifacts_path / "AcademicCreditLedger.sol" / "AcademicCreditLedger.json",
                "address": settings.ACADEMIC_CREDIT_ADDRESS
            },
            "contribution_registry": {
                "abi_path": artifacts_path / "ContributionRegistry.sol" / "ContributionRegistry.json",
                "address": settings.CONTRIBUTION_REGISTRY_ADDRESS
            }
        }
        
        for name, config in contract_configs.items():
            if config["address"] and config["abi_path"].exists():
                with open(config["abi_path"]) as f:
                    artifact = json.load(f)
                    self.contracts[name] = self.w3.eth.contract(
                        address=self.w3.to_checksum_address(config["address"]),
                        abi=artifact["abi"]
                    )
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to the blockchain."""
        return self.w3.is_connected()
    
    def get_block_number(self) -> int:
        """Get the current block number."""
        return self.w3.eth.block_number
    
    def get_balance(self, address: str) -> int:
        """Get the balance of an address in Wei."""
        return self.w3.eth.get_balance(self.w3.to_checksum_address(address))
    
    def _build_and_send_tx(self, contract_function, sender_address: str = None) -> Dict[str, Any]:
        """Build, sign, and send a transaction."""
        if not self.account:
            raise ValueError("No private key configured for transactions")
        
        sender = sender_address or self.account.address
        nonce = self.w3.eth.get_transaction_count(sender)
        
        tx = contract_function.build_transaction({
            "from": sender,
            "nonce": nonce,
            "gas": 500000,
            "gasPrice": 0,  # Private network with zero gas
            "chainId": settings.BESU_CHAIN_ID
        })
        
        signed_tx = self.w3.eth.account.sign_transaction(tx, settings.BESU_PRIVATE_KEY)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        mined = receipt.transactionHash.hex()
        demo_id = "0x" + secrets.token_hex(32)
        print(
            f"[SALF blockchain] console_transaction_id={demo_id} chain_transaction_id={mined} "
            f"status={'ok' if receipt.status == 1 else 'failed'}"
        )

        return {
            "tx_hash": mined,
            "block_number": receipt.blockNumber,
            "gas_used": receipt.gasUsed,
            "status": "success" if receipt.status == 1 else "failed"
        }
    
    # Academic Credit Ledger Functions
    async def submit_record(
        self,
        category: int,
        title: str,
        ipfs_hash: str,
        metadata_hash: str
    ) -> Dict[str, Any]:
        """Submit a new academic contribution to the blockchain."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        result = self._build_and_send_tx(
            contract.functions.submitRecord(category, title, ipfs_hash, metadata_hash)
        )
        
        # Get the contribution ID from events
        receipt = self.w3.eth.get_transaction_receipt(result["tx_hash"])
        logs = contract.events.ContributionSubmitted().process_receipt(receipt)
        if logs:
            result["contribution_id"] = logs[0]["args"]["contributionId"]
        
        return result
    
    async def record_evaluation(
        self,
        contribution_id: int,
        quality_score: int,
        novelty_percentage: int
    ) -> Dict[str, Any]:
        """Record AI evaluation results on the blockchain."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        return self._build_and_send_tx(
            contract.functions.recordEvaluation(contribution_id, quality_score, novelty_percentage)
        )
    
    async def validate_block(
        self,
        contribution_id: int,
        notes: str
    ) -> Dict[str, Any]:
        """Validate and finalize contribution credits."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        return self._build_and_send_tx(
            contract.functions.validateBlock(contribution_id, notes)
        )
    
    async def reject_contribution(
        self,
        contribution_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """Reject a contribution."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        return self._build_and_send_tx(
            contract.functions.rejectContribution(contribution_id, reason)
        )
    
    async def flag_contribution(
        self,
        contribution_id: int,
        reason: str
    ) -> Dict[str, Any]:
        """Flag a suspicious contribution."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        return self._build_and_send_tx(
            contract.functions.flagContribution(contribution_id, reason)
        )
    
    def get_contribution(self, contribution_id: int) -> Dict[str, Any]:
        """Get contribution details from blockchain."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        result = contract.functions.getContribution(contribution_id).call()
        return {
            "id": result[0],
            "faculty": result[1],
            "category": result[2],
            "title": result[3],
            "ipfs_hash": result[4],
            "metadata_hash": result[5],
            "submission_time": result[6],
            "status": result[7],
            "ai_quality_score": result[8],
            "novelty_percentage": result[9],
            "final_credits": result[10],
            "review_notes": result[11],
            "reviewer": result[12],
            "review_time": result[13]
        }
    
    def get_faculty_contributions(self, faculty_address: str) -> List[int]:
        """Get all contribution IDs for a faculty member."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        return contract.functions.getFacultyContributions(
            self.w3.to_checksum_address(faculty_address)
        ).call()

    def resolve_contribution_id_by_ipfs(
        self, ipfs_hash: str, faculty_address: Optional[str] = None
    ) -> Optional[int]:
        """Find contributionId by IPFS CID. Backend submitRecord uses msg.sender as on-chain faculty, so the operator key is tried first."""
        contract = self.contracts.get("academic_credit")
        if not contract or not ipfs_hash:
            return None

        candidates: List[str] = []
        if self.account:
            candidates.append(self.account.address)
        if faculty_address:
            candidates.append(faculty_address)

        seen = set()
        for addr in candidates:
            key = addr.lower()
            if key in seen:
                continue
            seen.add(key)
            try:
                raw_ids = contract.functions.getFacultyContributions(
                    self.w3.to_checksum_address(addr)
                ).call()
                for cid in raw_ids:
                    row = contract.functions.getContribution(int(cid)).call()
                    if row[4] == ipfs_hash:
                        return int(cid)
            except Exception:
                continue
        return None

    def get_contribution_chain_status(self, contribution_id: int) -> Optional[int]:
        """On-chain ContributionStatus enum value (0=PENDING, 1=UNDER_REVIEW, ...), or None."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            return None
        try:
            row = contract.functions.getContribution(int(contribution_id)).call()
            return int(row[7])
        except Exception:
            return None

    async def ensure_pending_moves_to_under_review(
        self,
        contribution_id: int,
        ai_quality_score: float,
        novelty_percentage: float,
    ) -> None:
        """validateBlock() requires UNDER_REVIEW; recordEvaluation() moves PENDING → UNDER_REVIEW."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            return
        try:
            row = contract.functions.getContribution(int(contribution_id)).call()
            if int(row[7]) != 0:
                return
        except Exception:
            return
        q = max(0, min(100, int(round(ai_quality_score or 0))))
        n = max(0, min(100, int(round(novelty_percentage or 0))))
        await self.record_evaluation(contribution_id, q, n)
    
    def get_faculty_total_credits(self, faculty_address: str) -> int:
        """Get total credits for a faculty member."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        return contract.functions.getFacultyTotalCredits(
            self.w3.to_checksum_address(faculty_address)
        ).call()
    
    def get_academic_portfolio(self, faculty_address: str) -> Dict[str, Any]:
        """Get academic portfolio summary."""
        contract = self.contracts.get("academic_credit")
        if not contract:
            raise ValueError("Academic Credit contract not loaded")
        
        result = contract.functions.getAcademicPortfolio(
            self.w3.to_checksum_address(faculty_address)
        ).call()
        
        return {
            "total_credits": result[0],
            "total_contributions": result[1],
            "validated_count": result[2],
            "pending_count": result[3],
            "rejected_count": result[4]
        }
    
    # Access Control Functions
    async def register_faculty(
        self,
        faculty_address: str,
        name: str,
        department: str,
        employee_id: str,
        institution: str
    ) -> Dict[str, Any]:
        """Register a new faculty member on the blockchain."""
        contract = self.contracts.get("access_control")
        if not contract:
            raise ValueError("Access Control contract not loaded")
        
        return self._build_and_send_tx(
            contract.functions.registerFaculty(
                self.w3.to_checksum_address(faculty_address),
                name,
                department,
                employee_id,
                institution
            )
        )
    
    async def create_department(
        self,
        code: str,
        name: str,
        hod_address: str
    ) -> Dict[str, Any]:
        """Create a new department on the blockchain."""
        contract = self.contracts.get("access_control")
        if not contract:
            raise ValueError("Access Control contract not loaded")
        
        return self._build_and_send_tx(
            contract.functions.createDepartment(
                code,
                name,
                self.w3.to_checksum_address(hod_address)
            )
        )
    
    def get_faculty_info(self, faculty_address: str) -> Dict[str, Any]:
        """Get faculty info from blockchain."""
        contract = self.contracts.get("access_control")
        if not contract:
            raise ValueError("Access Control contract not loaded")
        
        result = contract.functions.getFacultyInfo(
            self.w3.to_checksum_address(faculty_address)
        ).call()
        
        return {
            "name": result[0],
            "department": result[1],
            "employee_id": result[2],
            "institution": result[3],
            "registration_timestamp": result[4],
            "is_active": result[5],
            "total_credits": result[6]
        }
    
    def is_active_faculty(self, address: str) -> bool:
        """Check if an address is an active faculty member."""
        contract = self.contracts.get("access_control")
        if not contract:
            raise ValueError("Access Control contract not loaded")

        return contract.functions.isActiveFaculty(
            self.w3.to_checksum_address(address)
        ).call()

    def get_review_tx_hash(self, blockchain_id: int, status: str) -> Optional[str]:
        """
        Query blockchain event logs to retrieve the tx hash for a review action.
        Used to backfill review_tx_hash for contributions reviewed before that column existed.
        """
        contract = self.contracts.get("academic_credit")
        if not contract:
            return None

        event_map = {
            "validated": contract.events.ContributionValidated,
            "validate": contract.events.ContributionValidated,
            "rejected": contract.events.ContributionRejected,
            "reject": contract.events.ContributionRejected,
            "flagged": contract.events.ContributionFlagged,
            "flag": contract.events.ContributionFlagged,
        }
        event_fn = event_map.get(status)
        if not event_fn:
            return None

        try:
            logs = event_fn().get_logs(
                fromBlock=0,
                toBlock="latest",
                argument_filters={"contributionId": blockchain_id},
            )
            if logs:
                return logs[0].transactionHash.hex()
        except Exception:
            pass
        return None


# Singleton instance
blockchain_service = BlockchainService()
