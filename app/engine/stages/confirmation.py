"""
Confirmation Stage - مرحلة التأكيد النهائي وإنشاء الطلب والفاتورة في DB
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class ConfirmationStage(BaseStage):
    """مرحلة التأكيد النهائي وإنشاء الطلب"""
    
    stage = ConversationStage.FINAL_CONFIRMATION
    order = 10
    name_ar = "التأكيد النهائي"
    
    def __init__(self):
        super().__init__()
        self.order_repo = None
        self.invoice_repo = None
        self._init_repos()
    
    def _init_repos(self):
        """تهيئة repositories"""
        try:
            from app.db.repositories.order_repository import order_repository
            from app.db.repositories.invoice_repository import invoice_repository
            self.order_repo = order_repository
            self.invoice_repo = invoice_repository
        except Exception as e:
            self.logger.warning(f"Could not init repos: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "التأكيد النهائي",
            "description": "تأكيد الطلب وإنشاء الفاتورة",
            "required_action": "اسأل التأكيد النهائي قبل إنشاء الفاتورة"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة: تأكيد الطلب"""
        return ["order_confirmed"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        fields = {}
        if context.order_id:
            fields["order_confirmed"] = True
        return fields
    
    def can_go_back(self) -> bool:
        """يمكن العودة قبل التأكيد"""
        return True
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        
        # استخدام القيم الموجودة في العرض مباشرة (total_premium يتضمن الضريبة)
        total_premium = float(offer.get("total_premium", 0)) or float(offer.get("price", 0))
        gross_premium = float(offer.get("gross_premium", 0)) or (total_premium / 1.15)
        vat_amount = float(offer.get("vat_amount", 0)) or (total_premium - gross_premium)
        
        self.logger.info(f"💰 FINAL_CONFIRMATION - total_premium: {total_premium}, gross: {gross_premium}, vat: {vat_amount}")
        
        return f"""⚠️ أنت في مرحلة التأكيد النهائي.

🎯 ملخص الطلب:
- الشركة: {offer.get('company', 'غير محدد')}
- نوع التغطية: {offer.get('type', 'غير محدد')}
- القسط الأساسي: {gross_premium:,.2f} ريال
- ضريبة القيمة المضافة: {vat_amount:,.2f} ريال
- 💵 الإجمالي: {total_premium:,.2f} ريال

⛔ تعليمات صارمة:
- الإجمالي هو بالضبط {total_premium:,.2f} ريال (لا تحسبه من جديد!)
- لا تضيف ضريبة مرة أخرى - الإجمالي يتضمنها

✅ المطلوب:
قل فقط: "ممتاز! 🌟 الإجمالي {total_premium:,.2f} ريال شامل الضريبة. تبي أصدر لك الفاتورة الآن؟ ✅"
"""
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة التأكيد"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        if intent == UserIntent.CONFIRM:
            # إنشاء الطلب والفاتورة في DB
            self._create_order_and_invoice(context)
            
            self.logger.info("🧠 AI Transition: FINAL_CONFIRMATION -> INVOICE_ISSUED")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.INVOICE_ISSUED
            )
        
        if intent == UserIntent.REJECT:
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.ORDER_SUMMARY
            )
        
        return StageResponse(should_transition=False)
    
    def _create_order_and_invoice(self, context: ConversationContext):
        """إنشاء الطلب والفاتورة في قاعدة البيانات"""
        if not self.order_repo or not self.invoice_repo:
            self._generate_fallback_ids(context)
            return
        
        try:
            offer = context.selected_offer or {}
            # استخدام total_premium مباشرة (يتضمن الضريبة)
            total = float(offer.get("total_premium", 0)) or float(offer.get("price", 0))
            
            self.logger.info(f"📦 Creating order with total: {total}")
            
            # إنشاء الطلب
            order = self.order_repo.create_order(
                user_id=int(context.user_id) if context.user_id else 1,
                offer_id=offer.get("id", 1),
                company_id=offer.get("company_id", 1),
                service_id=offer.get("service_id", 1),
                total_price=total
            )
            
            if order and order.get("id"):
                context.order_id = order["id"]
                self.logger.info(f"✅ Created order in DB: {order.get('order_code')}")
                
                # إنشاء الفاتورة
                invoice = self.invoice_repo.create_invoice(
                    order_id=order["id"],
                    amount=total
                )
                
                if invoice and invoice.get("id"):
                    context.invoice_id = invoice["id"]
                    self.logger.info(f"✅ Created invoice in DB: {invoice.get('invoice_no')}")
                    
        except Exception as e:
            self.logger.error(f"Error creating order/invoice: {e}")
            self._generate_fallback_ids(context)
    
    def _generate_fallback_ids(self, context: ConversationContext):
        """IDs احتياطية"""
        import random
        if not context.order_id:
            context.order_id = random.randint(10000, 99999)
        if not context.invoice_id:
            context.invoice_id = random.randint(1000, 9999)


# Singleton instance
confirmation_stage = ConfirmationStage()
