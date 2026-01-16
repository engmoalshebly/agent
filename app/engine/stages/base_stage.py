"""
Base Stage - الكلاس الأساسي لجميع المراحل
كل مرحلة ترث من هذا الكلاس وتنفذ الدوال المطلوبة

النظام الاحترافي:
- كل مرحلة في ملف منفصل مع البرومبت الخاص بها
- لا يتم الانتقال للمرحلة التالية إلا عند اكتمال البيانات
- يمكن العودة لأي مرحلة سابقة
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import logging

from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext

logger = logging.getLogger(__name__)


@dataclass
class StageResponse:
    """استجابة المرحلة"""
    should_transition: bool
    next_stage: Optional[ConversationStage] = None
    extracted_data: Dict[str, Any] = None
    prompt_addition: str = ""
    error_message: str = ""  # رسالة خطأ إن وجدت
    special_response: Optional[str] = None  # رد مباشر بدلاً من استخدام LLM
    
    def __post_init__(self):
        if self.extracted_data is None:
            self.extracted_data = {}


class BaseStage(ABC):
    """
    الكلاس الأساسي لجميع المراحل
    
    كل مرحلة يجب أن تنفذ الدوال التالية:
    - get_stage_info(): معلومات المرحلة
    - get_required_fields(): الحقول المطلوبة
    - get_prompt_instructions(): تعليمات البرومبت
    - handle_intent(): معالجة النية وتحديد الانتقال
    
    المميزات:
    - التحقق من اكتمال البيانات قبل الانتقال
    - ملخص البيانات المجمعة
    - دعم العودة لمراحل سابقة
    """
    
    # يجب تعريف هذه القيمة في كل مرحلة
    stage: ConversationStage = None
    
    # ترتيب المرحلة (للعرض والتنقل)
    order: int = 0
    
    # اسم المرحلة بالعربي
    name_ar: str = ""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # =============================================
    # الدوال المطلوب تنفيذها (Abstract Methods)
    # =============================================
    
    @abstractmethod
    def get_stage_info(self) -> Dict[str, str]:
        """
        معلومات المرحلة للعرض
        Returns:
            Dict with keys: name, description, required_action
        """
        pass
    
    @abstractmethod
    def get_required_fields(self) -> List[str]:
        """
        قائمة الحقول المطلوبة للمرحلة
        يجب أن تُملأ جميعها قبل الانتقال للمرحلة التالية
        
        Returns:
            List of field names required for this stage
        """
        pass
    
    @abstractmethod
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        """
        تعليمات خاصة بالمرحلة للـ prompt
        Args:
            context: سياق المحادثة
        Returns:
            تعليمات نصية للـ LLM
        """
        pass
    
    @abstractmethod
    def handle_intent(
        self,
        intent,  # UserIntent from ai_intent_analyzer
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """
        معالجة النية وتحديد الانتقال
        Args:
            intent: نية المستخدم المحللة
            context: سياق المحادثة
            extracted_data: البيانات المستخرجة
        Returns:
            StageResponse يحدد الانتقال والبيانات
        """
        pass
    
    # =============================================
    # دوال التحقق من الاكتمال
    # =============================================
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """
        الحصول على الحقول المجمعة في هذه المرحلة
        يمكن override في كل مرحلة
        
        Returns:
            Dict of field_name: value
        """
        return {}
    
    def is_complete(self, context: ConversationContext) -> bool:
        """
        التحقق من اكتمال جميع الحقول المطلوبة
        لا يتم الانتقال للمرحلة التالية إلا إذا True
        
        Returns:
            True if all required fields are collected
        """
        required = self.get_required_fields()
        if not required:
            return True
        
        collected = self.get_collected_fields(context)
        return all(field in collected and collected[field] for field in required)
    
    def get_missing_fields(self, context: ConversationContext) -> List[str]:
        """
        الحصول على قائمة الحقول الناقصة
        
        Returns:
            List of missing field names
        """
        required = self.get_required_fields()
        collected = self.get_collected_fields(context)
        return [f for f in required if f not in collected or not collected[f]]
    
    def get_completion_percentage(self, context: ConversationContext) -> int:
        """
        نسبة اكتمال المرحلة (0-100)
        """
        required = self.get_required_fields()
        if not required:
            return 100
        
        collected = self.get_collected_fields(context)
        collected_count = sum(1 for f in required if f in collected and collected[f])
        return int((collected_count / len(required)) * 100)
    
    # =============================================
    # ملخصات البيانات
    # =============================================
    
    def get_collected_summary(self, context: ConversationContext) -> str:
        """
        ملخص البيانات المجمعة في هذه المرحلة (للعرض)
        
        Returns:
            نص ملخص البيانات
        """
        collected = self.get_collected_fields(context)
        if not collected:
            return "لا توجد بيانات"
        
        lines = []
        for field, value in collected.items():
            display_name = self._get_field_display_name(field)
            display_value = self._mask_sensitive_value(field, value)
            lines.append(f"• {display_name}: {display_value}")
        
        return "\n".join(lines)
    
    def get_missing_data(self, context: ConversationContext) -> str:
        """
        الحصول على وصف البيانات الناقصة
        """
        missing = self.get_missing_fields(context)
        if not missing:
            return "✅ جميع البيانات مكتملة"
        
        lines = []
        collected = self.get_collected_fields(context)
        
        for field in self.get_required_fields():
            display_name = self._get_field_display_name(field)
            if field in collected and collected[field]:
                value = self._mask_sensitive_value(field, collected[field])
                lines.append(f"✅ {display_name}: {value}")
            else:
                lines.append(f"❌ {display_name}: مطلوب")
        
        return "\n".join(lines)
    
    def get_status_line(self, context: ConversationContext) -> str:
        """
        سطر حالة المرحلة (للعرض في قائمة التقدم)
        """
        if self.is_complete(context):
            summary = self._get_short_summary(context)
            return f"✅ {self.order}. {self.name_ar} - مكتمل{summary}"
        else:
            required = self.get_required_fields()
            if required:
                missing = len(self.get_missing_fields(context))
                total = len(required)
                collected = total - missing
                return f"🔄 {self.order}. {self.name_ar} - جاري ({collected}/{total} حقول)"
            return f"🔄 {self.order}. {self.name_ar} - جاري"
    
    def _get_short_summary(self, context: ConversationContext) -> str:
        """ملخص قصير للعرض في قائمة التقدم"""
        return ""
    
    # =============================================
    # دوال مساعدة
    # =============================================
    
    def _get_field_display_name(self, field: str) -> str:
        """الحصول على اسم العرض للحقل بالعربي"""
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
            "phone": "رقم الجوال",
            "order_confirmed": "تأكيد الطلب",
            "invoice_id": "رقم الفاتورة",
            "payment_confirmed": "تأكيد الدفع",
        }
        return names.get(field, field)
    
    def _mask_sensitive_value(self, field: str, value: Any) -> str:
        """إخفاء البيانات الحساسة"""
        if field == "national_id" and isinstance(value, str) and len(value) >= 4:
            return "****" + value[-4:]
        if field == "phone" and isinstance(value, str) and len(value) >= 4:
            return value[:3] + "***" + value[-3:]
        return str(value)
    
    def can_go_back(self) -> bool:
        """
        هل يمكن العودة من هذه المرحلة؟
        عادة True إلا للمراحل النهائية مثل الدفع
        """
        return True
    
    # =============================================
    # Lifecycle Hooks
    # =============================================
    
    def on_enter(self, context: ConversationContext):
        """
        يُستدعى عند الدخول للمرحلة
        """
        self.logger.info(f"📍 Entering stage: {self.stage.value}")
    
    def on_exit(self, context: ConversationContext):
        """
        يُستدعى عند الخروج من المرحلة
        """
        self.logger.info(f"✅ Exiting stage: {self.stage.value}")
    
    def save_to_database(self, context: ConversationContext) -> bool:
        """
        حفظ البيانات في قاعدة البيانات
        """
        return True
    
    # =============================================
    # Full Stage Prompt (للاستخدام مع Master Orchestrator)
    # =============================================
    
    def get_full_stage_prompt(self, context: ConversationContext) -> str:
        """
        البرومبت الكامل للمرحلة يتضمن:
        - معلومات المرحلة
        - البيانات المجمعة والناقصة
        - التعليمات الخاصة
        """
        info = self.get_stage_info()
        missing_data = self.get_missing_data(context)
        instructions = self.get_prompt_instructions(context)
        
        prompt = f"""
═══════════════════════════════════════
⚠️ المرحلة الحالية: {info.get('name', self.name_ar)}
═══════════════════════════════════════

📋 الوصف: {info.get('description', '')}
🎯 المطلوب: {info.get('required_action', '')}

📊 حالة البيانات:
{missing_data}

═══════════════════════════════════════
📝 تعليمات المرحلة:
═══════════════════════════════════════
{instructions}

⚠️ تذكير مهم:
- لا تنتقل للمرحلة التالية إلا بعد اكتمال جميع البيانات المطلوبة
- إذا أراد العميل العودة لمرحلة سابقة، ساعده بذلك
- تعامل مع العميل كوسيط تأمين محترف وودود
"""
        return prompt
