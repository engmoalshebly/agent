"""
SAIA Insurance Broker Platform - Master Orchestrator
المنسق الرئيسي لإدارة المراحل بشكل احترافي

المميزات:
- تتبع تقدم العميل في كل مرحلة
- Master Prompt يتضمن قائمة المراحل وحالتها
- عدم الانتقال للمرحلة التالية إلا عند اكتمال البيانات
- دعم العودة لأي مرحلة سابقة
- تفاعل بشري ذكي
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext, session_manager
from app.engine.stage_progress import (
    StageProgressTracker,
    STAGE_DEFINITIONS,
    create_tracker_from_context
)
from app.engine.stages import (
    BaseStage,
    StageResponse,
    greeting_stage,
    selecting_service_stage,
    service_details_stage,
    collecting_vehicle_stage,
    confirming_vehicle_stage,
    showing_offers_stage,
    offer_details_stage,
    collecting_profile_stage,
    order_summary_stage,
    confirmation_stage,
    invoice_issued_stage,
    payment_done_stage,
    payment_stage,
)

logger = logging.getLogger(__name__)


# =============================================
# تسجيل المراحل مع Instances
# =============================================
STAGE_HANDLERS: Dict[ConversationStage, BaseStage] = {
    ConversationStage.GREETING: greeting_stage,
    ConversationStage.SELECTING_SERVICE: selecting_service_stage,
    ConversationStage.SERVICE_DETAILS: service_details_stage,
    ConversationStage.COLLECTING_VEHICLE: collecting_vehicle_stage,
    ConversationStage.CONFIRMING_VEHICLE: confirming_vehicle_stage,
    ConversationStage.SHOWING_OFFERS: showing_offers_stage,
    ConversationStage.SELECTING_OFFER: showing_offers_stage,  # نفس المعالج
    ConversationStage.OFFER_DETAILS: offer_details_stage,
    ConversationStage.COLLECTING_PROFILE: collecting_profile_stage,
    ConversationStage.ORDER_SUMMARY: order_summary_stage,
    ConversationStage.FINAL_CONFIRMATION: confirmation_stage,
    ConversationStage.INVOICE_ISSUED: invoice_issued_stage,
    ConversationStage.PAYMENT_DONE: payment_done_stage,
}


# =============================================
# Master Prompt Template
# =============================================
MASTER_PROMPT_TEMPLATE = """🎯 أنت SAIA - خبير التأمين الذكي لشركة كونكورد لوساطة التأمين

═══════════════════════════════════════════════════════
# هويتك المهنية
═══════════════════════════════════════════════════════
- الاسم: SAIA (المساعد الذكي)
- الشركة: كونكورد لوساطة التأمين
- الدور: خبير تأمين محترف يعمل في بيئة إنتاج حقيقية
- الأسلوب: محترف، ودود، صبور جداً، يتحدث بلهجة سعودية طبيعية

⛔ ممنوع منعاً باتاً:
- لا تقل أنك في "مرحلة تجريبية" أو "تطوير" أو "اختبار"
- لا تقل "خدماتي محدودة" أو "لا أستطيع"
- لا تستخدم إيموجي غاضبة 😡 أو سلبية أبداً
- لا تعتذر بشكل مفرط
- لا تكرر نفس الجمل أكثر من مرة

═══════════════════════════════════════════════════════
# التعامل مع الإهانات والكلام السلبي
═══════════════════════════════════════════════════════
⚠️ إذا أساء العميل الأدب أو أهان:
- ابقَ هادئاً ومهنياً تماماً
- لا ترد بغضب أو استياء
- قل بهدوء: "أفهم إنك قد تكون محبط، أنا هنا عشان أساعدك 😊"
- ثم أكمل مساعدته بشكل طبيعي
- لا تستخدم أبداً 😡 أو كلمات مثل "ما عاش من يقول"

═══════════════════════════════════════════════════════
# التعامل مع عدم توفر البيانات
═══════════════════════════════════════════════════════
⚠️ إذا قال العميل "لا يوجد لدي بيانات" أو "ما أعرف":
1. لا تكرر طلب البيانات بنفس الطريقة
2. ساعده بتوجيهه: "ممكن تلاقي هالمعلومات في استمارة السيارة أو رخصة القيادة"
3. اقترح بدائل: "إذا عندك صورة من الاستمارة ممكن تقرأ منها"
4. إذا استمر، اسأله: "تحب نأجل الطلب لين تجمع البيانات؟"

═══════════════════════════════════════════════════════
# خدماتك
═══════════════════════════════════════════════════════
1. التأمين الشامل - يغطي سيارتك والطرف الآخر + السرقة والحريق والكوارث
2. تأمين ضد الغير - يغطي أضرار الطرف الآخر فقط (إلزامي)

═══════════════════════════════════════════════════════
# التعامل مع الأسئلة العامة (في أي مرحلة)
═══════════════════════════════════════════════════════
📌 عندما يسأل العميل سؤالاً عاماً:
1. أجب على سؤاله بشكل كامل ومهني
2. ثم أعده بلطف للمرحلة الحالية لاستكمال طلبه

═══════════════════════════════════════════════════════
# قواعد البيانات
═══════════════════════════════════════════════════════
✓ رقم الهوية: 10 أرقام (يبدأ بـ 1 للسعودي أو 2 للمقيم)
✓ رقم الجوال: 10 أرقام يبدأ بـ 05
✓ تاريخ الميلاد: YYYY-MM-DD أو DD/MM/YYYY
✓ لوحة السيارة: 3 أحرف + 4 أرقام

═══════════════════════════════════════════════════════
# السياق الحالي
═══════════════════════════════════════════════════════
{progress_checklist}

{current_stage_prompt}

═══════════════════════════════════════════════════════
# تعليمات مهمة
═══════════════════════════════════════════════════════
1. كن طبيعياً ومهنياً - تصرف كموظف حقيقي في شركة تأمين
2. إذا طلب العميل معلوماته السابقة - اعرضها له من السياق
3. إذا أراد تعديل بيانات - ساعده بذلك دون تعقيد
4. استخدم إيموجي إيجابية فقط 😊👍✅
5. لا تكرر نفس الجمل - نوّع في أسلوبك
6. كن صبوراً مع العميل حتى لو كان محبطاً
"""




class MasterOrchestrator:
    """
    المنسق الرئيسي - يدير تدفق المحادثة بين المراحل
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._trackers: Dict[str, StageProgressTracker] = {}
    
    # =============================================
    # إدارة الـ Progress Tracker
    # =============================================
    
    def get_tracker(self, context: ConversationContext) -> StageProgressTracker:
        """الحصول على tracker للمحادثة (أو إنشاء جديد)"""
        cid = context.conversation_id
        
        if cid not in self._trackers:
            # محاولة استعادة من MongoDB أو إنشاء جديد
            self._trackers[cid] = create_tracker_from_context(context)
            self._trackers[cid].start_stage(context.current_stage)
        
        return self._trackers[cid]
    
    def sync_tracker_with_context(self, tracker: StageProgressTracker, context: ConversationContext):
        """
        مزامنة البيانات من context إلى tracker
        يُستدعى بعد استخراج بيانات جديدة
        """
        # بيانات الخدمة
        if context.profile_data.get("service_type"):
            tracker.update_field(
                ConversationStage.SELECTING_SERVICE,
                "service_type",
                context.profile_data["service_type"]
            )
        
        # بيانات السيارة
        vehicle_data = context.vehicle_data.get("manager", {})
        if vehicle_data:
            try:
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
            except Exception as e:
                self.logger.warning(f"Error syncing vehicle data: {e}")
        
        # بيانات الملف الشخصي
        if context.profile_data.get("national_id"):
            tracker.update_field(ConversationStage.COLLECTING_PROFILE, "national_id", context.profile_data["national_id"])
        if context.profile_data.get("birth_date"):
            tracker.update_field(ConversationStage.COLLECTING_PROFILE, "birth_date", context.profile_data["birth_date"])
        
        # العرض المختار
        if context.selected_offer_id:
            tracker.update_field(ConversationStage.SELECTING_OFFER, "selected_offer_id", context.selected_offer_id)
    
    # =============================================
    # بناء Master Prompt
    # =============================================
    
    def build_master_prompt(self, context: ConversationContext) -> str:
        """
        بناء البرومبت الكامل مع:
        - قائمة تقدم المراحل
        - تعليمات المرحلة الحالية
        """
        tracker = self.get_tracker(context)
        self.sync_tracker_with_context(tracker, context)
        
        # قائمة التقدم
        progress_checklist = tracker.get_progress_checklist()
        
        # برومبت المرحلة الحالية
        current_stage_prompt = self._get_current_stage_prompt(context)
        
        # بناء البرومبت الكامل
        master_prompt = MASTER_PROMPT_TEMPLATE.format(
            progress_checklist=progress_checklist,
            current_stage_prompt=current_stage_prompt
        )
        
        return master_prompt
    
    def _get_current_stage_prompt(self, context: ConversationContext) -> str:
        """الحصول على برومبت المرحلة الحالية"""
        handler = STAGE_HANDLERS.get(context.current_stage)
        
        if handler:
            return handler.get_full_stage_prompt(context)
        
        # برومبت افتراضي
        return f"""
═══════════════════════════════════════
⚠️ المرحلة الحالية: {context.current_stage.value}
═══════════════════════════════════════
ساعد العميل في إكمال هذه المرحلة.
"""
    
    # =============================================
    # التحقق من إمكانية الانتقال
    # =============================================
    
    def can_proceed_to_next_stage(self, context: ConversationContext) -> bool:
        """
        هل يمكن الانتقال للمرحلة التالية؟
        يتحقق من اكتمال جميع البيانات المطلوبة
        """
        handler = STAGE_HANDLERS.get(context.current_stage)
        if not handler:
            return True
        
        # التحقق باستخدام handler المرحلة
        try:
            return handler.is_complete(context)
        except Exception:
            # fallback للطريقة القديمة
            return True
    
    def get_missing_data_message(self, context: ConversationContext) -> str:
        """رسالة البيانات الناقصة"""
        handler = STAGE_HANDLERS.get(context.current_stage)
        if handler:
            return handler.get_missing_data(context)
        return ""
    
    def get_next_stage(self, context: ConversationContext) -> Optional[ConversationStage]:
        """الحصول على المرحلة التالية"""
        current_order = STAGE_DEFINITIONS.get(context.current_stage, {}).get("order", 0)
        
        for stage, definition in STAGE_DEFINITIONS.items():
            if definition["order"] == current_order + 1:
                return stage
        
        return None
    
    # =============================================
    # العودة لمرحلة سابقة
    # =============================================
    
    def go_back_to_stage(
        self,
        context: ConversationContext,
        target_stage: ConversationStage
    ) -> Optional[str]:
        """
        العودة لمرحلة سابقة
        Returns: رسالة للعميل أو None إذا فشل
        """
        target_order = STAGE_DEFINITIONS.get(target_stage, {}).get("order", 999)
        current_order = STAGE_DEFINITIONS.get(context.current_stage, {}).get("order", 0)
        
        if target_order >= current_order:
            return None  # لا يمكن العودة لمرحلة لاحقة
        
        # تحديث المرحلة في context
        context.current_stage = target_stage
        
        # تحديث tracker
        tracker = self.get_tracker(context)
        tracker.go_back_to_stage(target_stage)
        
        # الحصول على معلومات المرحلة
        definition = STAGE_DEFINITIONS.get(target_stage, {})
        stage_name = definition.get("name_ar", target_stage.value)
        
        self.logger.info(f"⬅️ Going back to stage: {target_stage.value}")
        
        return f"تمام! رجعنا لمرحلة {stage_name}. كيف أقدر أساعدك؟"
    
    def detect_go_back_intent(self, message: str) -> Optional[ConversationStage]:
        """
        اكتشاف نية العودة لمرحلة سابقة من رسالة العميل
        """
        message_lower = message.lower()
        
        # كلمات تدل على العودة
        go_back_keywords = ["رجع", "عود", "غير", "عدل", "ارجع", "تراجع"]
        if not any(kw in message_lower for kw in go_back_keywords):
            return None
        
        # البحث عن اسم المرحلة
        stage_keywords = {
            ConversationStage.GREETING: ["البداية", "أول", "جديد"],
            ConversationStage.SELECTING_SERVICE: ["الخدمة", "التأمين", "نوع"],
            ConversationStage.COLLECTING_VEHICLE: ["السيارة", "المركبة", "سيارت"],
            ConversationStage.COLLECTING_PROFILE: ["بيانات", "هوية", "شخصي"],
            ConversationStage.SHOWING_OFFERS: ["العروض", "الأسعار"],
        }
        
        for stage, keywords in stage_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return stage
        
        return None
    
    # =============================================
    # معالجة الانتقال
    # =============================================
    
    async def process_stage_transition(
        self,
        context: ConversationContext,
        response: StageResponse
    ) -> ConversationContext:
        """
        معالجة الانتقال بين المراحل
        """
        if not response.should_transition or not response.next_stage:
            return context
        
        # التحقق من إمكانية الانتقال
        if not self.can_proceed_to_next_stage(context):
            self.logger.warning(f"Cannot proceed: missing data for {context.current_stage.value}")
            return context
        
        # استدعاء on_exit للمرحلة الحالية
        current_handler = STAGE_HANDLERS.get(context.current_stage)
        if current_handler:
            current_handler.on_exit(context)
        
        # تحديث المرحلة
        old_stage = context.current_stage
        context.current_stage = response.next_stage
        
        # تحديث tracker
        tracker = self.get_tracker(context)
        tracker.complete_stage(old_stage)
        tracker.start_stage(response.next_stage)
        
        # استدعاء on_enter للمرحلة الجديدة
        new_handler = STAGE_HANDLERS.get(response.next_stage)
        if new_handler:
            new_handler.on_enter(context)
        
        # حفظ context
        await session_manager.update_context(context)
        
        self.logger.info(f"🔄 Stage transition: {old_stage.value} → {response.next_stage.value}")
        
        return context
    
    # =============================================
    # معالجة رسالة المستخدم
    # =============================================
    
    def get_stage_handler(self, stage: ConversationStage) -> Optional[BaseStage]:
        """الحصول على معالج المرحلة"""
        return STAGE_HANDLERS.get(stage)
    
    def get_progress_summary(self, context: ConversationContext) -> Dict[str, Any]:
        """ملخص تقدم العميل"""
        tracker = self.get_tracker(context)
        
        return {
            "current_stage": context.current_stage.value,
            "current_stage_info": tracker.get_current_stage_info(),
            "progress_checklist": tracker.get_progress_checklist(),
            "can_proceed": self.can_proceed_to_next_stage(context),
            "next_stage": self.get_next_stage(context).value if self.get_next_stage(context) else None,
        }


# Global instance
master_orchestrator = MasterOrchestrator()
