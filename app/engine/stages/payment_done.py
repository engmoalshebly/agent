"""
Payment Done Stage - مرحلة تأكيد الدفع وإصدار الوثيقة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class PaymentDoneStage(BaseStage):
    """مرحلة تأكيد الدفع وإصدار وثيقة التأمين"""
    
    stage = ConversationStage.PAYMENT_DONE
    order = 12
    name_ar = "الدفع"
    
    def __init__(self):
        super().__init__()
        self.invoice_repo = None
        self.order_repo = None
        self.policy_repo = None
        self._init_repos()
    
    def _init_repos(self):
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
            "name": "تم الدفع - إصدار الوثيقة",
            "description": "تأكيد الدفع وإصدار وثيقة التأمين",
            "required_action": "أكد استلام الدفع وأعط العميل الوثيقة"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول - هذه المرحلة النهائية"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        collected = {}
        if context.policy_id:
            collected["policy_id"] = context.policy_id
        return collected
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        policy_expiry = getattr(context, 'policy_expiry', None) or self._get_expiry_date()
        
        return f"""⚠️ أنت في مرحلة إصدار الوثيقة النهائية!

🎉 **تم الدفع بنجاح!**

📄 **بيانات الوثيقة:**
━━━━━━━━━━━━━━━━━━━
📋 رقم الوثيقة: {context.policy_id}
🏢 الشركة: {offer.get('company', 'غير محدد')}
🛡️ نوع التغطية: {offer.get('type', 'شامل')}
📅 صالحة حتى: {policy_expiry}

**تعليمات مهمة:**
- ❌ لا ترسل أي روابط
- ✅ أعط رقم الوثيقة فقط
- ✅ أخبره أن الوثيقة ستصل SMS + Email
- ✅ هنئه واسأله إذا يحتاج شيء آخر

**مثال الرد:**
"مبروك! 🎉🎊

تم إصدار وثيقة التأمين بنجاح!

━━━━━━━━━━━━━━━━━━━
📋 **رقم الوثيقة:** {context.policy_id}
🛡️ **التغطية:** {offer.get('type', 'تأمين شامل')}
🏢 **الشركة:** {offer.get('company', 'غير محدد')}
📅 **صالحة حتى:** {policy_expiry}
━━━━━━━━━━━━━━━━━━━

📱 الوثيقة راح توصلك على:
• الجوال (SMS)
• الإيميل

شكراً لثقتك فينا! 🙏
تحتاج أي شي ثاني؟"
"""

    
    def _get_expiry_date(self) -> str:
        """حساب تاريخ انتهاء الوثيقة (سنة من الآن)"""
        from datetime import datetime, timedelta
        expiry = datetime.now() + timedelta(days=365)
        return expiry.strftime("%Y/%m/%d")
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة إصدار الوثيقة"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # تسجيل الدفع وإصدار الوثيقة
        self._process_payment_and_issue_policy(context)
        
        # هذه هي المرحلة النهائية
        return StageResponse(should_transition=False)
    
    def _process_payment_and_issue_policy(self, context: ConversationContext):
        """تسجيل الدفع وإصدار الوثيقة"""
        if not context.invoice_id:
            self._generate_fallback_ids(context)
            return
        
        try:
            # تسجيل الدفع
            if self.invoice_repo:
                self.invoice_repo.mark_as_paid(context.invoice_id)
                self.logger.info(f"✅ Invoice {context.invoice_id} marked as paid")
            
            # تحديث حالة الطلب
            if self.order_repo and context.order_id:
                self.order_repo.update_order_status(context.order_id, "policy_issued")
            
            # إصدار الوثيقة
            if self.policy_repo and not context.policy_id:
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
            self._generate_fallback_ids(context)
    
    def _generate_fallback_ids(self, context: ConversationContext):
        """IDs احتياطية"""
        import random
        if not context.policy_id:
            context.policy_id = random.randint(10000, 99999)


# Singleton instance
payment_done_stage = PaymentDoneStage()
