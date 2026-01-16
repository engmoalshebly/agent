"""
SAIA Insurance Broker Platform - Stage Progress Tracker
تتبع تقدم العميل في المراحل مع قائمة تقدم احترافية
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from enum import Enum
import logging

from app.core.constants import ConversationStage

logger = logging.getLogger(__name__)


class StageStatus(str, Enum):
    """حالة المرحلة"""
    PENDING = "pending"           # لم تبدأ بعد
    IN_PROGRESS = "in_progress"   # جارية
    COMPLETED = "completed"       # مكتملة
    SKIPPED = "skipped"          # تم تخطيها


@dataclass
class StageProgressItem:
    """عنصر تقدم مرحلة واحدة"""
    stage: ConversationStage
    status: StageStatus = StageStatus.PENDING
    required_fields: List[str] = field(default_factory=list)
    collected_fields: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def completion_percentage(self) -> int:
        """نسبة اكتمال المرحلة"""
        if not self.required_fields:
            return 100 if self.status == StageStatus.COMPLETED else 0
        collected_count = sum(1 for f in self.required_fields if f in self.collected_fields)
        return int((collected_count / len(self.required_fields)) * 100)
    
    @property
    def is_complete(self) -> bool:
        """هل المرحلة مكتملة؟"""
        if not self.required_fields:
            return self.status == StageStatus.COMPLETED
        return all(f in self.collected_fields for f in self.required_fields)
    
    @property
    def missing_fields(self) -> List[str]:
        """الحقول الناقصة"""
        return [f for f in self.required_fields if f not in self.collected_fields]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage.value,
            "status": self.status.value,
            "required_fields": self.required_fields,
            "collected_fields": self.collected_fields,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "completion_percentage": self.completion_percentage,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageProgressItem":
        return cls(
            stage=ConversationStage(data["stage"]),
            status=StageStatus(data.get("status", "pending")),
            required_fields=data.get("required_fields", []),
            collected_fields=data.get("collected_fields", {}),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
        )


# تعريف المراحل وترتيبها مع الحقول المطلوبة
STAGE_DEFINITIONS = {
    ConversationStage.GREETING: {
        "order": 1,
        "name_ar": "الترحيب",
        "required_fields": [],
        "description": "الترحيب بالعميل وفهم طلبه"
    },
    ConversationStage.SELECTING_SERVICE: {
        "order": 2,
        "name_ar": "اختيار الخدمة",
        "required_fields": ["service_type"],
        "description": "اختيار نوع التأمين المطلوب"
    },
    ConversationStage.COLLECTING_VEHICLE: {
        "order": 3,
        "name_ar": "بيانات السيارة",
        "required_fields": ["vehicle_brand", "vehicle_model", "vehicle_year", "vehicle_value", "plate_no"],
        "description": "جمع بيانات السيارة كاملة"
    },
    ConversationStage.CONFIRMING_VEHICLE: {
        "order": 4,
        "name_ar": "تأكيد السيارة",
        "required_fields": ["vehicle_confirmed"],
        "description": "تأكيد صحة بيانات السيارة"
    },
    ConversationStage.SHOWING_OFFERS: {
        "order": 5,
        "name_ar": "عرض العروض",
        "required_fields": [],
        "description": "عرض عروض التأمين المتاحة"
    },
    ConversationStage.SELECTING_OFFER: {
        "order": 6,
        "name_ar": "اختيار العرض",
        "required_fields": ["selected_offer_id"],
        "description": "اختيار العرض المناسب"
    },
    ConversationStage.OFFER_DETAILS: {
        "order": 7,
        "name_ar": "تفاصيل العرض",
        "required_fields": ["offer_confirmed"],
        "description": "عرض وتأكيد تفاصيل العرض"
    },
    ConversationStage.COLLECTING_PROFILE: {
        "order": 8,
        "name_ar": "بيانات العميل",
        "required_fields": ["national_id", "birth_date"],
        "description": "جمع بيانات العميل الشخصية"
    },
    ConversationStage.ORDER_SUMMARY: {
        "order": 9,
        "name_ar": "ملخص الطلب",
        "required_fields": [],
        "description": "عرض ملخص الطلب الشامل"
    },
    ConversationStage.FINAL_CONFIRMATION: {
        "order": 10,
        "name_ar": "التأكيد النهائي",
        "required_fields": ["order_confirmed"],
        "description": "تأكيد الطلب النهائي"
    },
    ConversationStage.INVOICE_ISSUED: {
        "order": 11,
        "name_ar": "الفاتورة",
        "required_fields": ["invoice_id"],
        "description": "إصدار الفاتورة"
    },
    ConversationStage.PAYMENT_DONE: {
        "order": 12,
        "name_ar": "الدفع",
        "required_fields": ["payment_confirmed"],
        "description": "تأكيد الدفع"
    },
}


class StageProgressTracker:
    """
    متتبع تقدم المراحل - يتتبع حالة كل مرحلة وبياناتها
    """
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.stages: Dict[ConversationStage, StageProgressItem] = {}
        self.current_stage: ConversationStage = ConversationStage.GREETING
        self._initialize_stages()
    
    def _initialize_stages(self):
        """تهيئة جميع المراحل"""
        for stage, definition in STAGE_DEFINITIONS.items():
            self.stages[stage] = StageProgressItem(
                stage=stage,
                required_fields=definition["required_fields"].copy()
            )
    
    def start_stage(self, stage: ConversationStage):
        """بدء مرحلة"""
        if stage in self.stages:
            self.stages[stage].status = StageStatus.IN_PROGRESS
            self.stages[stage].started_at = datetime.now()
            self.current_stage = stage
            logger.info(f"📍 Started stage: {stage.value}")
    
    def complete_stage(self, stage: ConversationStage):
        """إكمال مرحلة"""
        if stage in self.stages:
            self.stages[stage].status = StageStatus.COMPLETED
            self.stages[stage].completed_at = datetime.now()
            logger.info(f"✅ Completed stage: {stage.value}")
    
    def update_field(self, stage: ConversationStage, field: str, value: Any):
        """تحديث حقل في مرحلة"""
        if stage in self.stages:
            self.stages[stage].collected_fields[field] = value
            logger.debug(f"📝 Updated {field} in {stage.value}: {value}")
    
    def can_proceed_to_next(self) -> bool:
        """هل يمكن الانتقال للمرحلة التالية؟"""
        current = self.stages.get(self.current_stage)
        if not current:
            return False
        return current.is_complete
    
    def get_next_stage(self) -> Optional[ConversationStage]:
        """الحصول على المرحلة التالية"""
        current_order = STAGE_DEFINITIONS.get(self.current_stage, {}).get("order", 0)
        for stage, definition in STAGE_DEFINITIONS.items():
            if definition["order"] == current_order + 1:
                return stage
        return None
    
    def go_back_to_stage(self, target_stage: ConversationStage) -> bool:
        """العودة لمرحلة سابقة"""
        target_order = STAGE_DEFINITIONS.get(target_stage, {}).get("order", 999)
        current_order = STAGE_DEFINITIONS.get(self.current_stage, {}).get("order", 0)
        
        if target_order < current_order:
            self.current_stage = target_stage
            self.stages[target_stage].status = StageStatus.IN_PROGRESS
            logger.info(f"⬅️ Going back to stage: {target_stage.value}")
            return True
        return False
    
    def get_stage_by_name_or_number(self, identifier: str) -> Optional[ConversationStage]:
        """الحصول على مرحلة برقمها أو اسمها"""
        # محاولة كرقم
        try:
            order = int(identifier)
            for stage, definition in STAGE_DEFINITIONS.items():
                if definition["order"] == order:
                    return stage
        except ValueError:
            pass
        
        # محاولة كاسم عربي
        identifier_lower = identifier.lower().strip()
        for stage, definition in STAGE_DEFINITIONS.items():
            if identifier_lower in definition["name_ar"].lower():
                return stage
            if identifier_lower in stage.value.lower():
                return stage
        
        return None
    
    def get_progress_checklist(self) -> str:
        """
        الحصول على قائمة التقدم المنسقة للبرومبت
        """
        lines = ["═══════════════════════════════════════", "📊 تقدم العميل في الخدمة:", "═══════════════════════════════════════"]
        
        for stage, definition in sorted(STAGE_DEFINITIONS.items(), key=lambda x: x[1]["order"]):
            item = self.stages.get(stage)
            order = definition["order"]
            name = definition["name_ar"]
            
            if not item:
                lines.append(f"⏳ {order}. {name} - في الانتظار")
                continue
            
            if item.status == StageStatus.COMPLETED:
                # مكتملة
                summary = self._get_stage_summary(item)
                lines.append(f"✅ {order}. {name} - مكتمل{summary}")
            elif item.status == StageStatus.IN_PROGRESS:
                # جارية
                if item.required_fields:
                    collected = len([f for f in item.required_fields if f in item.collected_fields])
                    total = len(item.required_fields)
                    lines.append(f"🔄 {order}. {name} - جاري ({collected}/{total} حقول)")
                    # عرض تفاصيل الحقول
                    for field in item.required_fields:
                        if field in item.collected_fields:
                            value = self._mask_sensitive(field, item.collected_fields[field])
                            lines.append(f"   ✓ {self._get_field_name(field)}: {value}")
                        else:
                            lines.append(f"   ✗ {self._get_field_name(field)}: مطلوب")
                else:
                    lines.append(f"🔄 {order}. {name} - جاري")
            elif item.status == StageStatus.SKIPPED:
                lines.append(f"⏭️ {order}. {name} - تم تخطيها")
            else:
                lines.append(f"⏳ {order}. {name} - في الانتظار")
        
        lines.append("═══════════════════════════════════════")
        return "\n".join(lines)
    
    def _get_stage_summary(self, item: StageProgressItem) -> str:
        """ملخص المرحلة المكتملة"""
        if item.stage == ConversationStage.SELECTING_SERVICE:
            service = item.collected_fields.get("service_type", "")
            return f" ({service})" if service else ""
        elif item.stage == ConversationStage.COLLECTING_VEHICLE:
            brand = item.collected_fields.get("vehicle_brand", "")
            model = item.collected_fields.get("vehicle_model", "")
            return f" ({brand} {model})" if brand and model else ""
        elif item.stage == ConversationStage.SELECTING_OFFER:
            offer_id = item.collected_fields.get("selected_offer_id", "")
            return f" (العرض {offer_id})" if offer_id else ""
        return ""
    
    def _get_field_name(self, field: str) -> str:
        """الحصول على اسم الحقل بالعربي"""
        names = {
            "service_type": "نوع الخدمة",
            "vehicle_brand": "نوع السيارة",
            "vehicle_model": "الموديل",
            "vehicle_year": "السنة",
            "vehicle_value": "القيمة",
            "plate_no": "رقم اللوحة",
            "vehicle_confirmed": "تأكيد السيارة",
            "selected_offer_id": "العرض المختار",
            "offer_confirmed": "تأكيد العرض",
            "national_id": "رقم الهوية",
            "birth_date": "تاريخ الميلاد",
            "order_confirmed": "تأكيد الطلب",
            "invoice_id": "رقم الفاتورة",
            "payment_confirmed": "تأكيد الدفع",
        }
        return names.get(field, field)
    
    def _mask_sensitive(self, field: str, value: Any) -> str:
        """إخفاء البيانات الحساسة"""
        if field == "national_id" and isinstance(value, str) and len(value) >= 4:
            return "****" + value[-4:]
        return str(value)
    
    def get_current_stage_info(self) -> Dict[str, Any]:
        """معلومات المرحلة الحالية"""
        definition = STAGE_DEFINITIONS.get(self.current_stage, {})
        item = self.stages.get(self.current_stage)
        
        return {
            "stage": self.current_stage.value,
            "order": definition.get("order", 0),
            "name_ar": definition.get("name_ar", ""),
            "description": definition.get("description", ""),
            "required_fields": definition.get("required_fields", []),
            "collected_fields": item.collected_fields if item else {},
            "missing_fields": item.missing_fields if item else [],
            "completion_percentage": item.completion_percentage if item else 0,
            "can_proceed": self.can_proceed_to_next(),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل للـ dict للحفظ في MongoDB"""
        return {
            "conversation_id": self.conversation_id,
            "current_stage": self.current_stage.value,
            "stages": {stage.value: item.to_dict() for stage, item in self.stages.items()},
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StageProgressTracker":
        """إنشاء من dict"""
        tracker = cls(data.get("conversation_id", ""))
        tracker.current_stage = ConversationStage(data.get("current_stage", "greeting"))
        
        stages_data = data.get("stages", {})
        for stage_value, item_data in stages_data.items():
            try:
                stage = ConversationStage(stage_value)
                tracker.stages[stage] = StageProgressItem.from_dict(item_data)
            except ValueError:
                logger.warning(f"Unknown stage: {stage_value}")
        
        return tracker


# مساعد لإنشاء tracker من context موجود
def create_tracker_from_context(context) -> StageProgressTracker:
    """إنشاء tracker من ConversationContext موجود"""
    tracker = StageProgressTracker(context.conversation_id)
    tracker.current_stage = context.current_stage
    
    # نقل البيانات من context للـ tracker
    if context.profile_data.get("service_type"):
        tracker.update_field(ConversationStage.SELECTING_SERVICE, "service_type", context.profile_data["service_type"])
        tracker.complete_stage(ConversationStage.SELECTING_SERVICE)
    
    if context.profile_data.get("national_id"):
        tracker.update_field(ConversationStage.COLLECTING_PROFILE, "national_id", context.profile_data["national_id"])
    if context.profile_data.get("birth_date"):
        tracker.update_field(ConversationStage.COLLECTING_PROFILE, "birth_date", context.profile_data["birth_date"])
    
    # بيانات السيارة
    vehicle_data = context.vehicle_data.get("manager", {})
    if vehicle_data:
        from app.engine.vehicle_manager import VehicleManager
        vm = VehicleManager.from_dict(vehicle_data)
        if vm.current_vehicle:
            v = vm.current_vehicle
            if v.brand:
                tracker.update_field(ConversationStage.COLLECTING_VEHICLE, "vehicle_brand", v.brand)
            if v.model:
                tracker.update_field(ConversationStage.COLLECTING_VEHICLE, "vehicle_model", v.model)
            if v.year:
                tracker.update_field(ConversationStage.COLLECTING_VEHICLE, "vehicle_year", v.year)
            if v.value:
                tracker.update_field(ConversationStage.COLLECTING_VEHICLE, "vehicle_value", v.value)
            if v.plate_no:
                tracker.update_field(ConversationStage.COLLECTING_VEHICLE, "plate_no", v.plate_no)
    
    if context.selected_offer_id:
        tracker.update_field(ConversationStage.SELECTING_OFFER, "selected_offer_id", context.selected_offer_id)
    
    # تحديث حالات المراحل بناءً على المرحلة الحالية
    current_order = STAGE_DEFINITIONS.get(context.current_stage, {}).get("order", 1)
    for stage, definition in STAGE_DEFINITIONS.items():
        if definition["order"] < current_order:
            tracker.complete_stage(stage)
        elif definition["order"] == current_order:
            tracker.start_stage(stage)
    
    return tracker
