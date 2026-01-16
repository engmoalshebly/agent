"""
Greeting Stage - مرحلة الترحيب
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class GreetingStage(BaseStage):
    """مرحلة الترحيب بالعميل"""
    
    stage = ConversationStage.GREETING
    order = 1
    name_ar = "الترحيب"
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "الترحيب",
            "description": "الترحيب بالعميل وفهم طلبه",
            "required_action": "رحب بالعميل واسأله كيف يمكن مساعدته"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول مطلوبة في مرحلة الترحيب"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """لا بيانات مجمعة في الترحيب"""
        return {}
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        return """⚠️ أنت في مرحلة الترحيب.
- رحب بالعميل بحرارة
- اسأله كيف يمكنك مساعدته
- لا تطلب أي بيانات شخصية في هذه المرحلة
- إذا سأل عن الخدمات المتوفرة، اعرضها له"""
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة الترحيب"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا سأل عن الخدمات أو أراد تأمين → انتقال لاختيار الخدمة
        if intent in (UserIntent.ASK_SERVICES, UserIntent.SELECT_SERVICE):
            self.logger.info("🧠 AI Transition: GREETING -> SELECTING_SERVICE")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.SELECTING_SERVICE
            )
        
        # البقاء في مرحلة الترحيب
        return StageResponse(should_transition=False)


# Singleton instance
greeting_stage = GreetingStage()
