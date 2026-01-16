"""
Stage Manager - مدير المراحل الاحترافي
يربط بين 14 مرحلة ويدير الانتقالات
"""
import logging
from typing import Dict, Optional

from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .stages.base_stage import BaseStage, StageResponse

logger = logging.getLogger(__name__)


class StageManager:
    """
    مدير المراحل الاحترافي - 14 مرحلة
    """
    
    def __init__(self):
        self.stages: Dict[ConversationStage, BaseStage] = {}
        self._register_stages()
    
    def _register_stages(self):
        """تسجيل جميع المراحل الـ 14"""
        from .stages import (
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
        )
        
        self.stages = {
            # التدفق الاحترافي (14 مرحلة)
            ConversationStage.GREETING: greeting_stage,
            ConversationStage.SHOWING_SERVICES: selecting_service_stage,  # نفس المرحلة
            ConversationStage.SELECTING_SERVICE: selecting_service_stage,
            ConversationStage.SERVICE_DETAILS: service_details_stage,
            ConversationStage.COLLECTING_VEHICLE: collecting_vehicle_stage,
            ConversationStage.CONFIRMING_VEHICLE: confirming_vehicle_stage,
            ConversationStage.SHOWING_OFFERS: showing_offers_stage,
            ConversationStage.SELECTING_OFFER: showing_offers_stage,  # نفس المرحلة
            ConversationStage.OFFER_DETAILS: offer_details_stage,
            ConversationStage.COLLECTING_PROFILE: collecting_profile_stage,
            ConversationStage.ORDER_SUMMARY: order_summary_stage,
            ConversationStage.FINAL_CONFIRMATION: confirmation_stage,
            ConversationStage.INVOICE_ISSUED: invoice_issued_stage,
            ConversationStage.PAYMENT_DONE: payment_done_stage,
            
            # Legacy stages (للتوافق)
            ConversationStage.AWAITING_SELECTION: showing_offers_stage,
            ConversationStage.CONFIRMATION: confirmation_stage,
            ConversationStage.PENDING_PAYMENT: invoice_issued_stage,
            ConversationStage.DONE: payment_done_stage,
        }
        
        logger.info(f"✅ Registered {len(self.stages)} stages for professional flow")
    
    def get_stage(self, stage: ConversationStage) -> Optional[BaseStage]:
        """الحصول على مرحلة معينة"""
        return self.stages.get(stage)
    
    def get_stage_info(self, stage: ConversationStage) -> Dict[str, str]:
        """الحصول على معلومات المرحلة"""
        stage_handler = self.get_stage(stage)
        if stage_handler:
            return stage_handler.get_stage_info()
        return {"name": "غير محدد", "description": "غير معروف", "required_action": "متابعة"}
    
    def get_prompt_instructions(self, stage: ConversationStage, context: ConversationContext) -> str:
        """الحصول على تعليمات الـ prompt للمرحلة"""
        stage_handler = self.get_stage(stage)
        if stage_handler:
            return stage_handler.get_prompt_instructions(context)
        return ""
    
    def handle_intent(self, stage: ConversationStage, intent, context: ConversationContext, extracted_data: Dict) -> StageResponse:
        """معالجة النية في المرحلة الحالية"""
        stage_handler = self.get_stage(stage)
        if stage_handler:
            response = stage_handler.handle_intent(intent, context, extracted_data)
            if response.should_transition and response.next_stage:
                stage_handler.on_exit(context)
                context.current_stage = response.next_stage
                new_handler = self.get_stage(response.next_stage)
                if new_handler:
                    new_handler.on_enter(context)
            return response
        return StageResponse(should_transition=False)
    
    def get_missing_data(self, stage: ConversationStage, context: ConversationContext) -> str:
        """الحصول على البيانات الناقصة للمرحلة"""
        stage_handler = self.get_stage(stage)
        if stage_handler:
            return stage_handler.get_missing_data(context)
        return ""


# Singleton instance
stage_manager = StageManager()
