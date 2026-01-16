"""
Policy Repository - إدارة وثائق التأمين
"""
import logging
import random
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)


class PolicyRepository:
    """Repository for insurance policy operations"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine(settings.database_url)
    
    def create_policy(
        self,
        order_id: int,
        user_id: int,
        vehicle_id: int,
        company_id: int
    ) -> Dict[str, Any]:
        """Create a new insurance policy"""
        try:
            policy_no = f"POL{random.randint(100000, 999999)}"
            start_date = datetime.now()
            end_date = start_date + timedelta(days=365)  # 1 year policy
            
            query = text("""
                INSERT INTO policies 
                (policy_no, order_id, user_id, vehicle_id, company_id, start_date, end_date, status)
                VALUES (:policy_no, :order_id, :user_id, :vehicle_id, :company_id, :start_date, :end_date, 'active')
                RETURNING id, policy_no, order_id, user_id, vehicle_id, start_date, end_date, status, created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "policy_no": policy_no,
                    "order_id": order_id,
                    "user_id": user_id,
                    "vehicle_id": vehicle_id,
                    "company_id": company_id,
                    "start_date": start_date,
                    "end_date": end_date
                })
                conn.commit()
                row = result.fetchone()
                
                if row:
                    policy = {
                        "id": row[0],
                        "policy_no": row[1],
                        "order_id": row[2],
                        "user_id": row[3],
                        "vehicle_id": row[4],
                        "start_date": str(row[5]),
                        "end_date": str(row[6]),
                        "status": row[7],
                        "created_at": str(row[8])
                    }
                    logger.info(f"Created policy: {policy['policy_no']}")
                    return policy
                    
        except Exception as e:
            logger.error(f"Error creating policy: {e}")
            return {}
        
        return {}
    
    def get_policy(self, policy_id: int) -> Optional[Dict[str, Any]]:
        """Get policy by ID"""
        try:
            query = text("""
                SELECT id, policy_no, order_id, user_id, vehicle_id, start_date, end_date, status, created_at
                FROM policies WHERE id = :policy_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"policy_id": policy_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "policy_no": row[1],
                        "order_id": row[2],
                        "user_id": row[3],
                        "vehicle_id": row[4],
                        "start_date": str(row[5]),
                        "end_date": str(row[6]),
                        "status": row[7],
                        "created_at": str(row[8])
                    }
        except Exception as e:
            logger.error(f"Error getting policy: {e}")
        
        return None
    
    def get_policy_by_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get policy by order ID"""
        try:
            query = text("""
                SELECT id, policy_no, order_id, user_id, vehicle_id, start_date, end_date, status, created_at
                FROM policies WHERE order_id = :order_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"order_id": order_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "policy_no": row[1],
                        "order_id": row[2],
                        "user_id": row[3],
                        "vehicle_id": row[4],
                        "start_date": str(row[5]),
                        "end_date": str(row[6]),
                        "status": row[7],
                        "created_at": str(row[8])
                    }
        except Exception as e:
            logger.error(f"Error getting policy by order: {e}")
        
        return None
    
    def get_policies_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all policies for a user"""
        try:
            query = text("""
                SELECT id, policy_no, order_id, user_id, vehicle_id, start_date, end_date, status, created_at
                FROM policies WHERE user_id = :user_id
                ORDER BY created_at DESC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"user_id": user_id})
                policies = []
                for row in result:
                    policies.append({
                        "id": row[0],
                        "policy_no": row[1],
                        "order_id": row[2],
                        "user_id": row[3],
                        "vehicle_id": row[4],
                        "start_date": str(row[5]),
                        "end_date": str(row[6]),
                        "status": row[7],
                        "created_at": str(row[8])
                    })
                return policies
        except Exception as e:
            logger.error(f"Error getting policies: {e}")
        
        return []


# Singleton instance
policy_repository = PolicyRepository()
