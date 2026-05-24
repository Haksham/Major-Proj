"""
SALF IPFS Service
InterPlanetary File System integration for decentralized document storage
"""
import hashlib
import io
from typing import Optional, Dict, Any, BinaryIO
import aiofiles
from pathlib import Path

try:
    import ipfshttpclient
    IPFS_AVAILABLE = True
except ImportError:
    IPFS_AVAILABLE = False

from app.core.config import settings


class IPFSService:
    """Service for interacting with IPFS for document storage."""
    
    def __init__(self):
        self._client = None
        self._connected = False
    
    def _get_client(self):
        """Get or create IPFS client connection."""
        if not IPFS_AVAILABLE:
            raise ImportError("ipfshttpclient is not installed")

        if self._client is None:
            try:
                self._client = ipfshttpclient.connect(
                    f"/ip4/{settings.IPFS_HOST}/tcp/{settings.IPFS_PORT}"
                )
                self._connected = True
            except Exception as e:
                self._connected = False
                raise ConnectionError(f"Failed to connect to IPFS at {settings.IPFS_HOST}:{settings.IPFS_PORT}: {e}")
        
        return self._client
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to IPFS."""
        if not self._connected:
            try:
                self._get_client()
            except Exception:
                return False
        return self._connected
    
    def calculate_sha256(self, data: bytes) -> str:
        """Calculate SHA-256 hash of data."""
        return hashlib.sha256(data).hexdigest()
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str
    ) -> Dict[str, Any]:
        """
        Upload a file to IPFS.
        
        Args:
            file_content: The file content as bytes
            filename: Original filename
            
        Returns:
            Dict with CID, size, and gateway URL
        """
        client = self._get_client()
        
        # Calculate metadata hash
        metadata_hash = self.calculate_sha256(file_content)
        
        # Upload to IPFS
        result = client.add(io.BytesIO(file_content))
        
        cid = result["Hash"]
        size = result["Size"]
        
        return {
            "cid": cid,
            "size": int(size),
            "filename": filename,
            "metadata_hash": metadata_hash,
            "gateway_url": f"{settings.IPFS_GATEWAY}{cid}"
        }
    
    async def upload_from_path(self, file_path: str) -> Dict[str, Any]:
        """Upload a file from local path to IPFS."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        async with aiofiles.open(file_path, 'rb') as f:
            content = await f.read()
        
        return await self.upload_file(content, path.name)
    
    async def get_file(self, cid: str) -> bytes:
        """
        Retrieve a file from IPFS by CID.
        
        Args:
            cid: The IPFS Content Identifier
            
        Returns:
            File content as bytes
        """
        client = self._get_client()
        return client.cat(cid)
    
    async def pin_file(self, cid: str) -> bool:
        """Pin a file to ensure it's not garbage collected."""
        client = self._get_client()
        try:
            client.pin.add(cid)
            return True
        except Exception:
            return False
    
    async def unpin_file(self, cid: str) -> bool:
        """Unpin a file."""
        client = self._get_client()
        try:
            client.pin.rm(cid)
            return True
        except Exception:
            return False
    
    def get_gateway_url(self, cid: str) -> str:
        """Get the HTTP gateway URL for a CID."""
        return f"{settings.IPFS_GATEWAY}{cid}"
    
    async def check_exists(self, cid: str) -> bool:
        """Check if a file exists in IPFS."""
        try:
            client = self._get_client()
            client.object.stat(cid)
            return True
        except Exception:
            return False
    
    async def get_stats(self, cid: str) -> Dict[str, Any]:
        """Get statistics about an IPFS object."""
        client = self._get_client()
        stats = client.object.stat(cid)
        return {
            "hash": stats["Hash"],
            "num_links": stats["NumLinks"],
            "block_size": stats["BlockSize"],
            "links_size": stats["LinksSize"],
            "data_size": stats["DataSize"],
            "cumulative_size": stats["CumulativeSize"]
        }
    
    def node_info(self) -> Dict[str, Any]:
        """Get IPFS node information."""
        client = self._get_client()
        info = client.id()
        return {
            "id": info["ID"],
            "public_key": info.get("PublicKey"),
            "addresses": info.get("Addresses", []),
            "agent_version": info.get("AgentVersion"),
            "protocol_version": info.get("ProtocolVersion")
        }


class MockIPFSService(IPFSService):
    """Mock IPFS service for development when IPFS is not available. Files are persisted to disk."""

    _STORE_DIR = Path(__file__).resolve().parent.parent.parent / ".mock_ipfs_store"

    def __init__(self):
        self._connected = True
        self._STORE_DIR.mkdir(parents=True, exist_ok=True)

    def _file_path(self, cid: str) -> Path:
        return self._STORE_DIR / cid

    def _base58btc_encode(self, data: bytes) -> str:
        alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
        num = int.from_bytes(data, "big")
        encoded = ""
        while num > 0:
            num, rem = divmod(num, 58)
            encoded = alphabet[rem] + encoded
        pad = sum(1 for b in data if b == 0)
        return ("1" * pad) + (encoded or "")

    def _mock_cid_v0(self, content: bytes) -> str:
        digest = hashlib.sha256(content).digest()
        multihash = b"\x12\x20" + digest
        return self._base58btc_encode(multihash)

    @property
    def is_connected(self) -> bool:
        return True

    async def upload_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        content_hash = self.calculate_sha256(file_content)
        mock_cid = self._mock_cid_v0(file_content)

        async with aiofiles.open(self._file_path(mock_cid), "wb") as f:
            await f.write(file_content)

        return {
            "cid": mock_cid,
            "size": len(file_content),
            "filename": filename,
            "metadata_hash": content_hash,
            "gateway_url": f"{settings.API_V1_PREFIX}/contributions/ipfs/{mock_cid}",
        }

    async def get_file(self, cid: str) -> bytes:
        path = self._file_path(cid)
        if not path.exists():
            raise FileNotFoundError(f"CID not found in local store: {cid}")
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def check_exists(self, cid: str) -> bool:
        return self._file_path(cid).exists()


def get_ipfs_service() -> IPFSService:
    """Factory function to get appropriate IPFS service."""
    try:
        service = IPFSService()
        if service.is_connected:
            return service
    except Exception:
        pass
    
    # Fall back to mock service
    return MockIPFSService()


# Singleton instance
ipfs_service = get_ipfs_service()
