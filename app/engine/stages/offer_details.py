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
        
        # 🔍 Logging: تسجيل العرض المختار للتشخيص
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"📋 OFFER_DETAILS - selected_offer: {offer}")
        
        # استخدام القيم الموجودة في العرض مباشرة (من قاعدة البيانات)
        gross_premium = float(offer.get("gross_premium", 0))
        ncd_discount_percent = float(offer.get("ncd_discount_percent", 0))
        ncd_discount_amount = float(offer.get("ncd_discount_amount", 0))
        premium_exc_vat = float(offer.get("premium_exc_vat", 0))
        vat_percent = float(offer.get("vat_percent", 15))
        vat_amount = float(offer.get("vat_amount", 0))
        total_premium = float(offer.get("total_premium", 0)) or float(offer.get("price", 0))
        
        # Fallback: إذا لم تكن القيم موجودة، احسبها من total_premium
        if not gross_premium and total_premium:
            gross_premium = total_premium / 1.15
            vat_amount = total_premium - gross_premium
            premium_exc_vat = gross_premium
        
        logger.info(f"💰 OFFER_DETAILS - total_premium: {total_premium}, gross_premium: {gross_premium}")
        
        # الرد الجاهز الذي يجب على Gemini نسخه بالضبط
        exact_response = f"""ممتاز اختيارك! 🌟 هذي تفاصيل المبلغ لعرض {offer.get('company', '')}:

✓ القسط الأساسي: {gross_premium:,.2f} ريال
✓ خصم عدم وجود مطالبات: {ncd_discount_amount:,.2f}- ({ncd_discount_percent:.0f}%)
✓ إجمالي بدون ضريبة: {premium_exc_vat:,.2f} ريال
✓ ضريبة القيمة المضافة: {vat_amount:,.2f} ريال

💰 الإجمالي: {total_premium:,.2f} ريال

تبي نكمل ونطلب بياناتك؟ 😊"""
        
        return f"""⛔⛔⛔ تعليمات صارمة جداً - اقرأها بدقة ⛔⛔⛔

أنت في مرحلة عرض تفاصيل المبلغ للعرض المختار.

## 🎯 العرض المختار:
- الشركة: {offer.get('company', 'غير محدد')}
- نوع التغطية: {self._get_coverage_name(offer.get('type', ''))}

## ⚠️ الأرقام الرسمية (لا تغيرها أبداً):
- القسط الأساسي: {gross_premium:,.2f} ريال
- خصم عدم وجود مطالبات: {ncd_discount_amount:,.2f} ريال ({ncd_discount_percent:.0f}%)
- إجمالي بدون ضريبة: {premium_exc_vat:,.2f} ريال
- ضريبة القيمة المضافة ({vat_percent:.0f}%): {vat_amount:,.2f} ريال
- 💵 الإجمالي النهائي: {total_premium:,.2f} ريال

## ⛔ ممنوع منعاً باتاً:
1. لا تحسب أي أرقام جديدة
2. لا تستخدم أي قيم غير المذكورة أعلاه
3. لا تنتقي أرقام من رأسك
4. لا تقرب الأرقام

## ✅ المطلوب:
انسخ هذا الرد بالضبط مع الأرقام المذكورة:

{exact_response}

## ⚠️ تحذير أخير:
إذا استخدمت أي رقم مختلف عن المذكور أعلاه، سيكون رداً خاطئاً.
الإجمالي النهائي يجب أن يكون بالضبط: {total_premium:,.2f} ريال"""
    
    def _get_coverage_name(self, coverage_type: str) -> str:
        """تحويل نوع التغطية لاسم عربي"""
        names = {
            "tpl": "تأمين ضد الغير",
            "comprehensive": "تأمين شامل",
            "vip": "تأمين VIP"
        }
        return names.get(coverage_type, coverage_type or "غير محدد")
    
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
