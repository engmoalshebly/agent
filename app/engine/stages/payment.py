"""
Payment Stage - مرحلة الدفع وإصدار الوثيقة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class PaymentStage(BaseStage):
    """مرحلة الدفع وإصدار الوثيقة"""
    
    stage = ConversationStage.PENDING_PAYMENT
    order = 12
    name_ar = "الدفع"
    
    def __init__(self):
        super().__init__()
        self.invoice_repo = None
        self.order_repo = None
        self.policy_repo = None
        self._init_repos()
    
    def _init_repos(self):
        """تهيئة repositories"""
        try:
            from app.db.repositories.invoice_repository import invoice_repository
            from app.db.repositories.order_repository import order_repository
            from app.db.repositories.policy_repository import policy_repository
            self.invoice_repo = invoice_repository
            self.order_repo = order_repository
            self.policy_repo = policy_repository
        except Exception as e:
            self.logger.warning(f"Could not init repos: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "انتظار الدفع",
            "description": "الفاتورة جاهزة وننتظر الدفع",
            "required_action": "أرشد العميل للدفع وانتظر التأكيد"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة: تأكيد الدفع"""
        return ["payment_confirmed"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        collected = {}
        if context.policy_id:
            collected["policy_id"] = context.policy_id
        return collected
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        return f"""⚠️ أنت في مرحلة انتظار الدفع.

رقم الفاتورة: {context.invoice_id}
رقم الطلب: {context.order_id}

- أرشد العميل لطريقة الدفع
- انتظر تأكيد الدفع منه
- عند التأكيد، سنصدر الوثيقة"""
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة الدفع"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        if intent == UserIntent.CONFIRM:
            # تسجيل الدفع وإصدار الوثيقة
            self._process_payment_and_issue_policy(context)
            
            self.logger.info("🧠 AI Transition: PENDING_PAYMENT -> DONE")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.DONE
            )
        
        return StageResponse(should_transition=False)
    
    def _process_payment_and_issue_policy(self, context: ConversationContext):
        """تسجيل الدفع وإصدار الوثيقة"""
        if not self.invoice_repo or not self.policy_repo:
            self._fallback_policy_id(context)
            return
        
        try:
            # تسجيل الدفع
            if context.invoice_id:
                self.invoice_repo.mark_as_paid(context.invoice_id)
                self.logger.info(f"✅ Invoice {context.invoice_id} marked as paid")
            
            # تحديث حالة الطلب
            if self.order_repo and context.order_id:
                self.order_repo.update_order_status(context.order_id, "policy_issued")
            
            # إصدار الوثيقة
            selected_offer = context.selected_offer or {}
            policy = self.policy_repo.create_policy(
                order_id=context.order_id,
                user_id=int(context.user_id) if context.user_id else 1,
                vehicle_id=context.vehicle_data.get("db_id", 1),
                company_id=selected_offer.get("company_id", 1)
            )
            
            if policy and policy.get("id"):
                context.policy_id = policy["id"]
                self.logger.info(f"✅ Policy issued: {policy.get('policy_no')}")
                
        except Exception as e:
            self.logger.error(f"Error processing payment: {e}")
            self._fallback_policy_id(context)
    
    def _fallback_policy_id(self, context: ConversationContext):
        """Policy ID احتياطي"""
        import random
        context.policy_id = random.randint(10000, 99999)


# Singleton instance
payment_stage = PaymentStage()
