"""
User Database Operations
Using PostgreSQL for user management
"""
import hashlib
import secrets
import uuid
from typing import Optional, Dict, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hash password with salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return hashed, salt


def verify_password(password: str, hashed: str, salt: str) -> bool:
    """Verify password against hash"""
    check_hash, _ = hash_password(password, salt)
    return check_hash == hashed


class UserRepository:
    """User database operations"""
    
    def __init__(self):
        self._connection = None
    
    async def _get_connection(self):
        """Get database connection"""
        if self._connection is None:
            import asyncpg
            self._connection = await asyncpg.connect(settings.database_url)
        return self._connection
    
    async def init_table(self):
        """Create users table if not exists"""
        conn = await self._get_connection()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                password_salt VARCHAR(64) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("Users table initialized")
    
    async def create_user(self, email: str, name: str, password: str) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            conn = await self._get_connection()
            
            # Check if email exists
            existing = await conn.fetchrow(
                "SELECT id FROM users WHERE email = $1",
                email.lower()
            )
            if existing:
                return None  # Email already exists
            
            # Hash password
            password_hash, password_salt = hash_password(password)
            
            # Create user
            user_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO users (id, email, name, password_hash, password_salt)
                VALUES ($1, $2, $3, $4, $5)
                """,
                uuid.UUID(user_id),
                email.lower(),
                name,
                password_hash,
                password_salt
            )
            
            return {
                "id": user_id,
                "email": email.lower(),
                "name": name
            }
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def authenticate(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user by email and password"""
        try:
            conn = await self._get_connection()
            
            user = await conn.fetchrow(
                """
                SELECT id, email, name, password_hash, password_salt
                FROM users WHERE email = $1
                """,
                email.lower()
            )
            
            if not user:
                return None
            
            if not verify_password(password, user["password_hash"], user["password_salt"]):
                return None
            
            return {
                "id": str(user["id"]),
                "email": user["email"],
                "name": user["name"]
            }
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            conn = await self._get_connection()
            
            user = await conn.fetchrow(
                "SELECT id, email, name FROM users WHERE id = $1",
                uuid.UUID(user_id)
            )
            
            if not user:
                return None
            
            return {
                "id": str(user["id"]),
                "email": user["email"],
                "name": user["name"]
            }
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None


# Global instance
user_repository = UserRepository()
