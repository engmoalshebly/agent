"""
Service Repository - جلب خدمات التأمين من قاعدة البيانات
"""
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)


class ServiceRepository:
    """Repository for insurance services from database"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine(settings.database_url)
    
    def get_active_services(self) -> List[Dict[str, Any]]:
        """Get all active insurance services from database"""
        try:
            query = text("""
                SELECT id, service_code, name_ar, name_en, description, is_active
                FROM insurance_services 
                WHERE is_active = true
                ORDER BY id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query)
                services = []
                for row in result:
                    services.append({
                        "id": row[0],
                        "code": row[1],
                        "name_ar": row[2],
                        "name_en": row[3],
                        "description": row[4],
                        "is_active": row[5]
                    })
                logger.info(f"Fetched {len(services)} active services from DB")
                return services
                
        except Exception as e:
            logger.error(f"Error fetching services: {e}")
            return []
    
    def get_service_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Get service by its code"""
        try:
            query = text("""
                SELECT id, service_code, name_ar, name_en, description
                FROM insurance_services 
                WHERE service_code = :code AND is_active = true
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"code": code})
                row = result.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "code": row[1],
                        "name_ar": row[2],
                        "name_en": row[3],
                        "description": row[4]
                    }
        except Exception as e:
            logger.error(f"Error fetching service by code: {e}")
        
        return None
    
    def get_service_by_id(self, service_id: int) -> Optional[Dict[str, Any]]:
        """Get service by its ID"""
        try:
            query = text("""
                SELECT id, service_code, name_ar, name_en, description
                FROM insurance_services 
                WHERE id = :id AND is_active = true
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"id": service_id})
                row = result.fetchone()
                if row:
                    return {
                        "id": row[0],
                        "code": row[1],
                        "name_ar": row[2],
                        "name_en": row[3],
                        "description": row[4]
                    }
        except Exception as e:
            logger.error(f"Error fetching service by id: {e}")
        
        return None
    
    def format_services_for_display(self, services: List[Dict]) -> str:
        """Format services list for display to user"""
        if not services:
            return "لا توجد خدمات متوفرة حالياً"
        
        lines = ["الخدمات المتوفرة:"]
        for i, svc in enumerate(services, 1):
            name = svc.get("name_ar", svc.get("name_en", ""))
            desc = svc.get("description", "")
            lines.append(f"{i}. {name}")
            if desc:
                lines.append(f"   {desc}")
        
        return "\n".join(lines)


# Singleton instance
service_repository = ServiceRepository()
