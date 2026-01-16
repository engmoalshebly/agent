"""
Selecting Service Stage - مرحلة اختيار نوع التأمين
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class SelectingServiceStage(BaseStage):
    """مرحلة اختيار نوع التأمين"""
    
    stage = ConversationStage.SELECTING_SERVICE
    order = 2
    name_ar = "اختيار الخدمة"
    
    def __init__(self):
        super().__init__()
        self.service_repo = None
        self._init_service_repo()
    
    def _init_service_repo(self):
        """تهيئة repository الخدمات"""
        try:
            from app.db.repositories.service_repository import service_repository
            self.service_repo = service_repository
        except Exception as e:
            self.logger.warning(f"Could not init service repo: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "اختيار نوع التأمين",
            "description": "عرض الخدمات المتوفرة ومساعدة العميل في الاختيار",
            "required_action": "اعرض الخدمات المتوفرة من قاعدة البيانات ودع العميل يختار"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة: نوع الخدمة"""
        return ["service_type"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        fields = {}
        if context.profile_data.get("service_type"):
            fields["service_type"] = context.profile_data["service_type"]
        return fields
    
    def _get_short_summary(self, context: ConversationContext) -> str:
        """ملخص قصير للقائمة"""
        service_type = context.profile_data.get("service_type", "")
        return f" ({service_type})" if service_type else ""
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        # جلب الخدمات من DB
        services_text = self._get_services_from_db()
        
        return f"""⚠️ أنت في مرحلة اختيار نوع التأمين.

الخدمات المتوفرة من قاعدة البيانات:
{services_text}

- اعرض الخدمات للعميل بشكل ودود
- ساعده في الاختيار إذا كان محتاراً
- لا تطلب بياناته الشخصية حتى يختار نوع التأمين"""
    
    def _get_services_from_db(self) -> str:
        """جلب الخدمات من قاعدة البيانات"""
        if not self.service_repo:
            return "لا توجد خدمات متوفرة"
        
        try:
            services = self.service_repo.get_active_services()
            if not services:
                return "لا توجد خدمات متوفرة"
            
            lines = []
            for i, svc in enumerate(services, 1):
                name = svc.get("name_ar", svc.get("code", ""))
                desc = svc.get("description", "")
                lines.append(f"{i}. {name}")
                if desc:
                    lines.append(f"   ({desc})")
            
            return "\n".join(lines)
        except Exception as e:
            self.logger.error(f"Error fetching services: {e}")
            return "لا توجد خدمات متوفرة"
    
    def get_available_services(self) -> list:
        """الحصول على قائمة الخدمات المتوفرة"""
        if not self.service_repo:
            return []
        return self.service_repo.get_active_services()
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة اختيار الخدمة"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا اختار نوع تأمين
        if intent == UserIntent.SELECT_SERVICE:
            service_type = extracted_data.get("service_type")
            service_name = extracted_data.get("service_name")
            
            if service_type or service_name:
                # حفظ نوع التأمين المختار
                context.profile_data["service_type"] = service_type or service_name
                
                # تهيئة VehicleManager
                from app.engine.vehicle_manager import VehicleManager
                if "manager" not in context.vehicle_data:
                    vm = VehicleManager(context.conversation_id)
                    vm.start_new_vehicle()
                    context.vehicle_data["manager"] = vm.to_dict()
                
                # التدفق الجديد: ننتقل لجمع بيانات السيارة أولاً
                self.logger.info(f"🧠 AI Transition: SELECTING_SERVICE -> COLLECTING_VEHICLE (service: {service_type})")
                
                return StageResponse(
                    should_transition=True,
                    next_stage=ConversationStage.COLLECTING_VEHICLE,
                    extracted_data={"service_type": service_type or service_name}
                )
        
        # إذا سأل عن الخدمات - إضافة معلومات للـ prompt
        if intent == UserIntent.ASK_SERVICES:
            services_text = self._get_services_from_db()
            return StageResponse(
                should_transition=False,
                prompt_addition=f"\n\n=== الخدمات المتوفرة ===\n{services_text}"
            )
        
        return StageResponse(should_transition=False)


# Singleton instance
selecting_service_stage = SelectingServiceStage()
