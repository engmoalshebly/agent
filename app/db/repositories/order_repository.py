"""
Order Repository - إدارة الطلبات
"""
import logging
import random
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)


class OrderRepository:
    """Repository for insurance order operations"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine(settings.database_url)
    
    def create_order(
        self,
        user_id: int,
        offer_id: int,
        company_id: int,
        service_id: int,
        total_price: float
    ) -> Dict[str, Any]:
        """Create a new insurance order"""
        try:
            order_code = f"ORD{random.randint(100000, 999999)}"
            
            query = text("""
                INSERT INTO insurance_orders 
                (order_code, user_id, offer_id, company_id, service_id, total_price, status)
                VALUES (:order_code, :user_id, :offer_id, :company_id, :service_id, :total_price, 'awaiting_confirmation')
                RETURNING id, order_code, user_id, offer_id, total_price, status, created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "order_code": order_code,
                    "user_id": user_id,
                    "offer_id": offer_id,
                    "company_id": company_id,
                    "service_id": service_id,
                    "total_price": total_price
                })
                conn.commit()
                row = result.fetchone()
                
                if row:
                    order = {
                        "id": row[0],
                        "order_code": row[1],
                        "user_id": row[2],
                        "offer_id": row[3],
                        "total_price": float(row[4]) if row[4] else 0,
                        "status": row[5],
                        "created_at": str(row[6])
                    }
                    logger.info(f"Created order: {order['order_code']}")
                    return order
                    
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            return {}
        
        return {}
    
    def get_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get order by ID"""
        try:
            query = text("""
                SELECT id, order_code, user_id, offer_id, total_price, status, created_at
                FROM insurance_orders WHERE id = :order_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"order_id": order_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "order_code": row[1],
                        "user_id": row[2],
                        "offer_id": row[3],
                        "total_price": float(row[4]) if row[4] else 0,
                        "status": row[5],
                        "created_at": str(row[6])
                    }
        except Exception as e:
            logger.error(f"Error getting order: {e}")
        
        return None
    
    def update_order_status(self, order_id: int, status: str) -> bool:
        """Update order status"""
        try:
            query = text("""
                UPDATE insurance_orders SET status = :status, updated_at = CURRENT_TIMESTAMP
                WHERE id = :order_id
            """)
            
            with self.engine.connect() as conn:
                conn.execute(query, {"order_id": order_id, "status": status})
                conn.commit()
                logger.info(f"Updated order {order_id} status to: {status}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
        
        return False
    
    def get_orders_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all orders for a user"""
        try:
            query = text("""
                SELECT id, order_code, user_id, offer_id, total_price, status, created_at
                FROM insurance_orders WHERE user_id = :user_id
                ORDER BY created_at DESC
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"user_id": user_id})
                orders = []
                for row in result:
                    orders.append({
                        "id": row[0],
                        "order_code": row[1],
                        "user_id": row[2],
                        "offer_id": row[3],
                        "total_price": float(row[4]) if row[4] else 0,
                        "status": row[5],
                        "created_at": str(row[6])
                    })
                return orders
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
        
        return []


# Singleton instance
order_repository = OrderRepository()
