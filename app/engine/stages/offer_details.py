"""
Offer Details Stage - مرحلة تفاصيل المبلغ
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class OfferDetailsStage(BaseStage):
    """مرحلة عرض تفاصيل المبلغ والأسعار"""
    
    stage = ConversationStage.OFFER_DETAILS
    order = 7
    name_ar = "تفاصيل العرض"
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "تفاصيل المبلغ",
            "description": "عرض تفصيل الأسعار والضرائب",
            "required_action": "اعرض تفاصيل المبلغ كاملة واسأل العميل عن المتابعة"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول مطلوبة - فقط عرض"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        return {}
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        price = float(offer.get("price", 0))
        
        # حساب التفاصيل
        base_premium = price / 1.15  # السعر قبل الضريبة
        vat = price - base_premium
        discount = 0  # يمكن حسابه من DB
        
        return f"""⚠️ أنت في مرحلة عرض تفاصيل المبلغ.

🎯 العرض المختار:
- الشركة: {offer.get('company', 'غير محدد')}
- نوع التغطية: {offer.get('type', 'غير محدد')}

💰 تفاصيل المبلغ:
✓ القسط الأساسي: {base_premium:,.2f} ريال
✓ خصم عدم وجود مطالبات: {discount:,.2f}- ريال (0%)
✓ إجمالي المبلغ بدون ضريبة: {base_premium:,.2f} ريال
✓ ضريبة القيمة المضافة (15%): {vat:,.2f} ريال
━━━━━━━━━━━━━━━━━━
💵 إجمالي المبلغ: {price:,.2f} ريال

تعليمات مهمة:
- اعرض التفاصيل بشكل مرتب (كما في النموذج)
- اسأل: "تبي نكمل ونطلب بياناتك الشخصية؟ 😊"
- كن متحمساً ومشجعاً

مثال:
"ممتاز اختيارك! 🌟 هذي تفاصيل المبلغ:

✓ القسط الأساسي: 2,874.05 ريال
✓ خصم عدم وجود مطالبات: 0.00- (0%)
✓ إجمالي بدون ضريبة: 2,874.05 ريال
✓ ضريبة القيمة المضافة: 431.11 ريال

💰 الإجمالي: 3,305.16 ريال

تبي نكمل ونطلب بياناتك؟ 😊"
"""
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة تفاصيل المبلغ"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا أراد المتابعة
        if intent == UserIntent.CONFIRM:
            self.logger.info("🧠 AI Transition: OFFER_DETAILS -> COLLECTING_PROFILE")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.COLLECTING_PROFILE
            )
        
        # إذا أراد اختيار عرض آخر
        if intent == UserIntent.REJECT:
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.SHOWING_OFFERS
            )
        
        return StageResponse(should_transition=False)


# Singleton instance
offer_details_stage = OfferDetailsStage()
