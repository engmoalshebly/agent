"""
Invoice Repository - إدارة الفواتير
"""
import logging
import random
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)


class InvoiceRepository:
    """Repository for invoice operations"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine(settings.database_url)
    
    def create_invoice(
        self,
        order_id: int,
        amount: float,
        provider: str = "demo"
    ) -> Dict[str, Any]:
        """Create a new invoice"""
        try:
            invoice_no = f"INV{random.randint(100000, 999999)}"
            expires_at = datetime.now() + timedelta(hours=24)
            
            query = text("""
                INSERT INTO invoices (order_id, invoice_no, amount, provider, status, expires_at)
                VALUES (:order_id, :invoice_no, :amount, :provider, 'unpaid', :expires_at)
                RETURNING id, invoice_no, order_id, amount, status, expires_at, created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "order_id": order_id,
                    "invoice_no": invoice_no,
                    "amount": amount,
                    "provider": provider,
                    "expires_at": expires_at
                })
                conn.commit()
                row = result.fetchone()
                
                if row:
                    invoice = {
                        "id": row[0],
                        "invoice_no": row[1],
                        "order_id": row[2],
                        "amount": float(row[3]) if row[3] else 0,
                        "status": row[4],
                        "expires_at": str(row[5]),
                        "created_at": str(row[6])
                    }
                    logger.info(f"Created invoice: {invoice['invoice_no']}")
                    return invoice
                    
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {}
        
        return {}
    
    def get_invoice(self, invoice_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice by ID"""
        try:
            query = text("""
                SELECT id, invoice_no, order_id, amount, status, expires_at, paid_at, created_at
                FROM invoices WHERE id = :invoice_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"invoice_id": invoice_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "invoice_no": row[1],
                        "order_id": row[2],
                        "amount": float(row[3]) if row[3] else 0,
                        "status": row[4],
                        "expires_at": str(row[5]) if row[5] else None,
                        "paid_at": str(row[6]) if row[6] else None,
                        "created_at": str(row[7])
                    }
        except Exception as e:
            logger.error(f"Error getting invoice: {e}")
        
        return None
    
    def get_invoice_by_order(self, order_id: int) -> Optional[Dict[str, Any]]:
        """Get invoice by order ID"""
        try:
            query = text("""
                SELECT id, invoice_no, order_id, amount, status, expires_at, paid_at, created_at
                FROM invoices WHERE order_id = :order_id
                ORDER BY created_at DESC LIMIT 1
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"order_id": order_id})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "invoice_no": row[1],
                        "order_id": row[2],
                        "amount": float(row[3]) if row[3] else 0,
                        "status": row[4],
                        "expires_at": str(row[5]) if row[5] else None,
                        "paid_at": str(row[6]) if row[6] else None,
                        "created_at": str(row[7])
                    }
        except Exception as e:
            logger.error(f"Error getting invoice by order: {e}")
        
        return None
    
    def mark_as_paid(self, invoice_id: int) -> bool:
        """Mark invoice as paid"""
        try:
            query = text("""
                UPDATE invoices 
                SET status = 'paid', paid_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = :invoice_id
            """)
            
            with self.engine.connect() as conn:
                conn.execute(query, {"invoice_id": invoice_id})
                conn.commit()
                logger.info(f"Invoice {invoice_id} marked as paid")
                return True
                
        except Exception as e:
            logger.error(f"Error marking invoice as paid: {e}")
        
        return False


# Singleton instance
invoice_repository = InvoiceRepository()
