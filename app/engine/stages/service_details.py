"""
Service Details Stage - مرحلة شرح تفاصيل الخدمة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class ServiceDetailsStage(BaseStage):
    """مرحلة شرح تفاصيل الخدمة المختارة"""
    
    stage = ConversationStage.SERVICE_DETAILS
    order = 3
    name_ar = "تفاصيل الخدمة"
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "تفاصيل الخدمة",
            "description": "شرح تفاصيل الخدمة المختارة للعميل",
            "required_action": "اشرح مميزات الخدمة بأسلوب تسويقي جذاب"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول مطلوبة - فقط عرض"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        return {}
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        service_type = context.profile_data.get("service_type", "")
        
        return f"""⚠️ أنت في مرحلة شرح تفاصيل الخدمة.

🎯 الخدمة المختارة: {service_type}

تعليمات مهمة:
- اشرح مميزات الخدمة بأسلوب تسويقي جذاب
- اذكر الفوائد الرئيسية
- اجعل العميل متحمساً للمتابعة
- اسأله "تبي نكمل ونسجل بيانات سيارتك؟ 😊"

مثال على الرد:
"ممتاز اختيارك! 🌟 التأمين الشامل يغطي:
✓ الحوادث بجميع أنواعها
✓ السرقة والحريق
✓ سيارة بديلة
✓ مساعدة على الطريق 24/7

تبي نكمل ونسجل بيانات سيارتك؟ 🚗"
"""
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة تفاصيل الخدمة"""
        from app.engine.ai_intent_analyzer import UserIntent
        from app.engine.vehicle_manager import VehicleManager
        
        # إذا أراد المتابعة
        if intent == UserIntent.CONFIRM:
            # تهيئة VehicleManager
            if "manager" not in context.vehicle_data:
                vm = VehicleManager(context.conversation_id)
                vm.start_new_vehicle()
                context.vehicle_data["manager"] = vm.to_dict()
            
            self.logger.info("🧠 AI Transition: SERVICE_DETAILS -> COLLECTING_VEHICLE")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.COLLECTING_VEHICLE
            )
        
        return StageResponse(should_transition=False)


# Singleton instance
service_details_stage = ServiceDetailsStage()
