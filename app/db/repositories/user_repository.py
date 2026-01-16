"""
User Repository - إدارة بيانات المستخدمين
"""
import logging
from typing import Optional, Dict, Any
from datetime import date
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data operations"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine(settings.database_url)
    
    def create_user(
        self,
        national_id: str,
        birth_date: str,
        phone: Optional[str] = None,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new user or return existing one"""
        try:
            # Check if user exists
            existing = self.get_user_by_national_id(national_id)
            if existing:
                logger.info(f"User already exists with national_id: {national_id}")
                return existing
            
            # Generate user code
            import random
            user_code = f"USR{random.randint(100000, 999999)}"
            
            query = text("""
                INSERT INTO users (user_code, national_id, birth_date, phone, full_name)
                VALUES (:user_code, :national_id, :birth_date, :phone, :full_name)
                RETURNING id, user_code, national_id, birth_date, phone, full_name, created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "user_code": user_code,
                    "national_id": national_id,
                    "birth_date": birth_date,
                    "phone": phone,
                    "full_name": full_name or "عميل"
                })
                conn.commit()
                row = result.fetchone()
                
                if row:
                    user = {
                        "id": row[0],
                        "user_code": row[1],
                        "national_id": row[2],
                        "birth_date": str(row[3]) if row[3] else None,
                        "phone": row[4],
                        "full_name": row[5],
                        "created_at": str(row[6])
                    }
                    logger.info(f"Created user: {user['user_code']}")
                    return user
                    
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return {}
        
        return {}
    
    def get_user_by_national_id(self, national_id: str) -> Optional[Dict[str, Any]]:
        """Get user by national ID"""
        try:
            query = text("""
                SELECT id, user_code, national_id, birth_date, phone, full_name, created_at
                FROM users WHERE national_id = :national_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"national_id": national_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "user_code": row[1],
                        "national_id": row[2],
                        "birth_date": str(row[3]) if row[3] else None,
                        "phone": row[4],
                        "full_name": row[5],
                        "created_at": str(row[6])
                    }
        except Exception as e:
            logger.error(f"Error getting user: {e}")
        
        return None
    
    def get_user_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Get user by phone number"""
        try:
            query = text("""
                SELECT id, user_code, national_id, birth_date, phone, full_name, created_at
                FROM users WHERE phone = :phone
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"phone": phone})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "user_code": row[1],
                        "national_id": row[2],
                        "birth_date": str(row[3]) if row[3] else None,
                        "phone": row[4],
                        "full_name": row[5],
                        "created_at": str(row[6])
                    }
        except Exception as e:
            logger.error(f"Error getting user by phone: {e}")
        
        return None


# Singleton instance
user_repository = UserRepository()
