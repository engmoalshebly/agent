"""
Invoice Issued Stage - مرحلة إصدار الفاتورة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class InvoiceIssuedStage(BaseStage):
    """مرحلة إصدار الفاتورة وإرشاد العميل للدفع"""
    
    stage = ConversationStage.INVOICE_ISSUED
    order = 11
    name_ar = "الفاتورة"
    
    def __init__(self):
        super().__init__()
        self.order_repo = None
        self.invoice_repo = None
        self._init_repos()
    
    def _init_repos(self):
        try:
            from app.db.repositories.order_repository import order_repository
            from app.db.repositories.invoice_repository import invoice_repository
            self.order_repo = order_repository
            self.invoice_repo = invoice_repository
        except Exception as e:
            self.logger.warning(f"Could not init repos: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "إصدار الفاتورة",
            "description": "إصدار رقم الفاتورة وإرشاد العميل للدفع",
            "required_action": "أعط العميل رقم الفاتورة وأرشده لطريقة الدفع"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة: دفع الفاتورة"""
        return ["payment_confirmed"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        collected = {}
        if context.invoice_id:
            collected["invoice_id"] = context.invoice_id
        if context.order_id:
            collected["order_id"] = context.order_id
        return collected
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        price = offer.get("price", 0)
        vat = price * 0.15
        total = price + vat
        
        sadad_number = getattr(context, 'sadad_number', None) or self._generate_sadad()
        biller_code = getattr(context, 'biller_code', None) or "177"
        
        return f"""⚠️ أنت في مرحلة إصدار الفاتورة.

📄 **بيانات الفاتورة:**
━━━━━━━━━━━━━━━━━━━
📋 رقم الفاتورة: {context.invoice_id}
📋 رقم الطلب: {context.order_id}
💰 المبلغ الإجمالي: {total:,.0f} ريال

💳 **بيانات السداد:**
━━━━━━━━━━━━━━━━━━━
🏦 رقم المُفوتر: {biller_code}
🔢 رقم السداد: {sadad_number}
⏰ صلاحية السداد: 24 ساعة

**تعليمات مهمة:**
- ❌ لا ترسل أي روابط
- ✅ أعط فقط رقم السداد ورقم المُفوتر
- ✅ أخبره طرق الدفع: سداد، تطبيق البنك، الصراف
- ✅ اسأله إذا دفع

**مثال الرد:**
"تمام! 🎉 تم إصدار فاتورتك بنجاح!

📋 **رقم الفاتورة:** {context.invoice_id}
💰 **المبلغ:** {total:,.0f} ريال

━━━━━━━━━━━━━━━━━━━
💳 **بيانات السداد:**
🏦 رقم المُفوتر: {biller_code}
🔢 رقم السداد: {sadad_number}
━━━━━━━━━━━━━━━━━━━

✅ طرق الدفع:
• سداد
• تطبيق البنك
• الصراف الآلي

⏰ صلاحية الدفع: 24 ساعة

بعد ما تدفع قولي 'تم الدفع' وأكمل لك! 😊"
"""

    def _generate_sadad(self) -> str:
        """توليد رقم سداد افتراضي"""
        import random
        return f"177{random.randint(10000000000, 99999999999)}"
    

    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة إصدار الفاتورة"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا أكد الدفع
        if intent == UserIntent.CONFIRM:
            self.logger.info("🧠 AI Transition: INVOICE_ISSUED -> PAYMENT_DONE")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.PAYMENT_DONE
            )
        
        return StageResponse(should_transition=False)


# Singleton instance
invoice_issued_stage = InvoiceIssuedStage()
