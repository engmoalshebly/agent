"""
SAIA Insurance Broker Platform - Idempotency Manager
Prevents duplicate operations (e.g., double invoice creation)
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Optional, Dict, Any
import logging

from .constants import IDEMPOTENCY_WINDOW_MINUTES

logger = logging.getLogger(__name__)


@dataclass
class IdempotencyResult:
    """Result of idempotency check"""
    is_duplicate: bool
    is_processing: bool = False
    original_result: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class IdempotencyManager:
    """
    Manages idempotency keys to prevent duplicate operations.
    
    Usage:
        idempotency = IdempotencyManager(db)
        result = await idempotency.check_and_lock(order_id, "invoice", "create")
        
        if result.is_duplicate:
            return result.original_result
        
        # Do the actual work...
        invoice = await create_invoice(...)
        
        await idempotency.mark_completed(key, invoice.dict())
    """
    
    def __init__(self, db=None):
        self.db = db
        self._cache: Dict[str, Dict] = {}  # In-memory cache for demo
    
    @staticmethod
    def generate_key(entity_id: str, entity_type: str, action: str) -> str:
        """Generate unique idempotency key"""
        raw = f"{entity_id}:{entity_type}:{action}"
        return sha256(raw.encode()).hexdigest()[:16]
    
    async def check_and_lock(
        self, 
        entity_id: str, 
        entity_type: str, 
        action: str
    ) -> IdempotencyResult:
        """
        Check if operation already exists and lock if new.
        
        Returns:
            IdempotencyResult with is_duplicate=True if already exists
        """
        key = self.generate_key(entity_id, entity_type, action)
        
        # Check in-memory cache first (for demo)
        existing = self._cache.get(key)
        
        if existing:
            if existing["status"] == "completed":
                logger.info(f"Idempotency hit: {key} - returning cached result")
                return IdempotencyResult(
                    is_duplicate=True,
                    original_result=existing.get("result"),
                    message="تم تنفيذ هذه العملية مسبقاً"
                )
            elif existing["status"] == "processing":
                logger.info(f"Idempotency: {key} - operation in progress")
                return IdempotencyResult(
                    is_duplicate=True,
                    is_processing=True,
                    message="العملية قيد التنفيذ حالياً"
                )
        
        # Check if expired
        if existing:
            expires_at = existing.get("expires_at")
            if expires_at and datetime.now() > expires_at:
                # Expired, remove and allow new operation
                del self._cache[key]
                existing = None
        
        # Lock the operation
        self._cache[key] = {
            "status": "processing",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=IDEMPOTENCY_WINDOW_MINUTES)
        }
        
        logger.info(f"Idempotency: {key} - new operation locked")
        return IdempotencyResult(is_duplicate=False)
    
    async def mark_completed(self, entity_id: str, entity_type: str, action: str, result: Dict[str, Any]):
        """Mark operation as completed with result"""
        key = self.generate_key(entity_id, entity_type, action)
        
        if key in self._cache:
            self._cache[key]["status"] = "completed"
            self._cache[key]["result"] = result
            self._cache[key]["completed_at"] = datetime.now()
            logger.info(f"Idempotency: {key} - marked completed")
    
    async def release_lock(self, entity_id: str, entity_type: str, action: str):
        """Release lock on failure"""
        key = self.generate_key(entity_id, entity_type, action)
        
        if key in self._cache:
            del self._cache[key]
            logger.info(f"Idempotency: {key} - lock released")
    
    def clear_expired(self):
        """Clear expired entries from cache"""
        now = datetime.now()
        expired_keys = [
            k for k, v in self._cache.items()
            if v.get("expires_at") and now > v["expires_at"]
        ]
        for key in expired_keys:
            del self._cache[key]


# Global instance
idempotency_manager = IdempotencyManager()
