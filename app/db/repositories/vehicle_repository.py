"""
Vehicle Repository - إدارة بيانات السيارات
"""
import logging
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from app.config import settings

logger = logging.getLogger(__name__)


class VehicleRepository:
    """Repository for vehicle data operations"""
    
    def __init__(self):
        from sqlalchemy import create_engine
        self.engine = create_engine(settings.database_url)
    
    def create_vehicle(
        self,
        user_id: int,
        plate_no: str,
        brand: str,
        model: str,
        model_year: int,
        vehicle_value: float
    ) -> Dict[str, Any]:
        """Create a new vehicle"""
        try:
            # Check if vehicle exists
            existing = self.get_vehicle_by_plate(plate_no)
            if existing:
                logger.info(f"Vehicle already exists with plate: {plate_no}")
                return existing
            
            query = text("""
                INSERT INTO vehicles (user_id, plate_no, brand, model, model_year, vehicle_value)
                VALUES (:user_id, :plate_no, :brand, :model, :model_year, :vehicle_value)
                RETURNING id, user_id, plate_no, brand, model, model_year, vehicle_value, created_at
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "user_id": user_id,
                    "plate_no": plate_no,
                    "brand": brand,
                    "model": model,
                    "model_year": model_year,
                    "vehicle_value": vehicle_value
                })
                conn.commit()
                row = result.fetchone()
                
                if row:
                    vehicle = {
                        "id": row[0],
                        "user_id": row[1],
                        "plate_no": row[2],
                        "brand": row[3],
                        "model": row[4],
                        "model_year": row[5],
                        "vehicle_value": float(row[6]) if row[6] else 0,
                        "created_at": str(row[7])
                    }
                    logger.info(f"Created vehicle: {vehicle['plate_no']}")
                    return vehicle
                    
        except Exception as e:
            logger.error(f"Error creating vehicle: {e}")
            return {}
        
        return {}
    
    def get_vehicle_by_plate(self, plate_no: str) -> Optional[Dict[str, Any]]:
        """Get vehicle by plate number"""
        try:
            query = text("""
                SELECT id, user_id, plate_no, brand, model, model_year, vehicle_value, created_at
                FROM vehicles WHERE plate_no = :plate_no
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"plate_no": plate_no})
                row = result.fetchone()
                
                if row:
                    return {
                        "id": row[0],
                        "user_id": row[1],
                        "plate_no": row[2],
                        "brand": row[3],
                        "model": row[4],
                        "model_year": row[5],
                        "vehicle_value": float(row[6]) if row[6] else 0,
                        "created_at": str(row[7])
                    }
        except Exception as e:
            logger.error(f"Error getting vehicle: {e}")
        
        return None
    
    def get_vehicles_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all vehicles for a user"""
        try:
            query = text("""
                SELECT id, user_id, plate_no, brand, model, model_year, vehicle_value, created_at
                FROM vehicles WHERE user_id = :user_id
            """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {"user_id": user_id})
                vehicles = []
                for row in result:
                    vehicles.append({
                        "id": row[0],
                        "user_id": row[1],
                        "plate_no": row[2],
                        "brand": row[3],
                        "model": row[4],
                        "model_year": row[5],
                        "vehicle_value": float(row[6]) if row[6] else 0,
                        "created_at": str(row[7])
                    })
                return vehicles
        except Exception as e:
            logger.error(f"Error getting vehicles: {e}")
        
        return []


# Singleton instance
vehicle_repository = VehicleRepository()
