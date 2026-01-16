"""
SAIA Insurance Broker Platform - Vehicle Manager
Handles multiple vehicles per session
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.constants import MAX_VEHICLES_PER_SESSION

logger = logging.getLogger(__name__)


@dataclass
class VehicleData:
    """Vehicle data structure"""
    index: int
    plate_no: Optional[str] = None
    serial_no: Optional[str] = None
    custom_card_no: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None
    value: Optional[float] = None
    color: Optional[str] = None
    registration_type: str = "plate"  # plate, serial, custom
    collected_at: datetime = field(default_factory=datetime.now)
    is_complete: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "plate_no": self.plate_no,
            "serial_no": self.serial_no,
            "brand": self.brand,
            "model": self.model,
            "year": self.year,
            "value": self.value,
            "color": self.color,
            "registration_type": self.registration_type,
            "is_complete": self.is_complete
        }
    
    def check_completeness(self) -> bool:
        """Check if all required fields are collected
        
        الحقول المطلوبة:
        - brand (النوع) ✅ مطلوب
        - year (السنة) ✅ مطلوب  
        - value (القيمة) ✅ مطلوب
        - plate_no أو serial_no (المعرف) ✅ مطلوب
        - model (الموديل) ⚪ اختياري (قد يكون مدمج مع brand)
        """
        required_fields = [
            self.brand,           # مطلوب
            self.year,            # مطلوب
            self.value            # مطلوب
        ]
        
        # Either plate or serial must be provided
        has_identifier = bool(self.plate_no or self.serial_no or self.custom_card_no)
        
        # model اختياري - قد يكون مدمج مع brand مثل "هيونداي سوناتا"
        self.is_complete = has_identifier and all(required_fields)
        return self.is_complete
    
    def get_display_name(self) -> str:
        """Get display name for vehicle"""
        if self.brand and self.model:
            year_str = f" {self.year}" if self.year else ""
            return f"{self.brand} {self.model}{year_str}"
        return f"السيارة {self.index}"
    
    def get_identifier(self) -> str:
        """Get vehicle identifier (plate/serial)"""
        return self.plate_no or self.serial_no or self.custom_card_no or "غير محدد"


class VehicleManager:
    """
    Manages multiple vehicles for a single session/customer.
    
    Features:
    - Add/edit vehicles
    - Track completion status
    - Support up to MAX_VEHICLES_PER_SESSION
    - Generate summary for display
    """
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.vehicles: List[VehicleData] = []
        self.current_index: int = 0
    
    @property
    def current_vehicle(self) -> Optional[VehicleData]:
        """Get current vehicle being edited"""
        if 0 <= self.current_index < len(self.vehicles):
            return self.vehicles[self.current_index]
        return None
    
    @property
    def vehicle_count(self) -> int:
        """Number of vehicles added"""
        return len(self.vehicles)
    
    @property
    def complete_vehicles(self) -> List[VehicleData]:
        """Get list of complete vehicles"""
        return [v for v in self.vehicles if v.is_complete]
    
    def can_add_more(self) -> bool:
        """Check if more vehicles can be added"""
        return len(self.vehicles) < MAX_VEHICLES_PER_SESSION
    
    def start_new_vehicle(self) -> VehicleData:
        """Start collecting new vehicle"""
        if not self.can_add_more():
            raise ValueError(f"الحد الأقصى للسيارات هو {MAX_VEHICLES_PER_SESSION}")
        
        new_vehicle = VehicleData(index=len(self.vehicles) + 1)
        self.vehicles.append(new_vehicle)
        self.current_index = len(self.vehicles) - 1
        
        logger.info(f"Started new vehicle #{new_vehicle.index} for conversation {self.conversation_id}")
        return new_vehicle
    
    def update_current(self, **kwargs) -> VehicleData:
        """Update current vehicle with provided fields"""
        vehicle = self.current_vehicle
        if not vehicle:
            vehicle = self.start_new_vehicle()
        
        for key, value in kwargs.items():
            if hasattr(vehicle, key) and value is not None:
                setattr(vehicle, key, value)
        
        vehicle.check_completeness()
        return vehicle
    
    def get_missing_fields(self) -> List[str]:
        """Get list of missing required fields for current vehicle"""
        vehicle = self.current_vehicle
        if not vehicle:
            return ["registration_type"]
        
        missing = []
        
        # Check identifier
        if not (vehicle.plate_no or vehicle.serial_no or vehicle.custom_card_no):
            missing.append("رقم اللوحة/التسلسلي")
        
        if not vehicle.brand:
            missing.append("الشركة المصنعة")
        if not vehicle.model:
            missing.append("الموديل")
        if not vehicle.year:
            missing.append("سنة الصنع")
        if not vehicle.value:
            missing.append("القيمة التقديرية")
        
        return missing
    
    def get_next_field_to_ask(self) -> Optional[str]:
        """Get next field to ask about"""
        missing = self.get_missing_fields()
        return missing[0] if missing else None
    
    def get_summary(self, mask: bool = False) -> str:
        """Get summary of all vehicles"""
        if not self.vehicles:
            return "لا توجد سيارات"
        
        lines = []
        for v in self.vehicles:
            status = "✅" if v.is_complete else "⏳"
            identifier = v.get_identifier()
            if mask and v.plate_no:
                from app.core.security import DataMasker
                identifier = DataMasker.mask_plate(v.plate_no)
            
            name = v.get_display_name()
            lines.append(f"{status} {v.index}. {name} ({identifier})")
        
        return "\n".join(lines)
    
    def get_vehicles_for_quotes(self) -> List[Dict[str, Any]]:
        """Get complete vehicles ready for quote requests"""
        return [v.to_dict() for v in self.complete_vehicles]
    
    def should_ask_for_another(self) -> bool:
        """Should we ask if user wants another vehicle?"""
        if not self.vehicles:
            return False
        
        current = self.current_vehicle
        if not current or not current.is_complete:
            return False
        
        return self.can_add_more()
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "conversation_id": self.conversation_id,
            "vehicles": [v.to_dict() for v in self.vehicles],
            "current_index": self.current_index
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VehicleManager":
        """Deserialize from dictionary"""
        manager = cls(data.get("conversation_id", ""))
        manager.current_index = data.get("current_index", 0)
        
        for v_data in data.get("vehicles", []):
            vehicle = VehicleData(
                index=v_data.get("index", 1),
                plate_no=v_data.get("plate_no"),
                serial_no=v_data.get("serial_no"),
                brand=v_data.get("brand"),
                model=v_data.get("model"),
                year=v_data.get("year"),
                value=v_data.get("value"),
                color=v_data.get("color"),
                registration_type=v_data.get("registration_type", "plate"),
                is_complete=v_data.get("is_complete", False)
            )
            manager.vehicles.append(vehicle)
        
        return manager
