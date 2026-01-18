"""
Order Summary Stage - مرحلة ملخص الطلب الشامل مع تكامل DB
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class OrderSummaryStage(BaseStage):
    """مرحلة ملخص الطلب الشامل قبل التأكيد النهائي"""
    
    stage = ConversationStage.ORDER_SUMMARY
    order = 9
    name_ar = "ملخص الطلب"
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "ملخص الطلب",
            "description": "عرض ملخص شامل للطلب (سيارة + عميل + عرض)",
            "required_action": "اعرض جميع البيانات واسأل العميل عن التأكيد"
        }
    
    def get_required_fields(self) -> List[str]:
        """لا توجد حقول مطلوبة - فقط عرض"""
        return []
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        return {}
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        vehicle_info = self._get_vehicle_summary(context)
        profile_info = self._get_profile_summary(context)
        offer_info = self._get_offer_summary(context)
        
        return f"""⚠️ أنت في مرحلة ملخص الطلب الشامل.

📋 ملخص الطلب الكامل:

═══════════════════════════════════
👤 بيانات العميل:
{profile_info}

═══════════════════════════════════
🚗 بيانات السيارة:
{vehicle_info}

═══════════════════════════════════
🛡️ تفاصيل التأمين:
{offer_info}
═══════════════════════════════════

تعليمات مهمة:
- اعرض الملخص بشكل مرتب وجميل
- اسأل: "هل كل شي صحيح وتبي نعتمد الطلب؟ ✅"
- إذا أراد التعديل، اسأله أي قسم

مثال:
"تمام! 📋 خليني ألخص لك الطلب كامل:

👤 بياناتك:
   • الهوية: ****7890
   • الميلاد: 1992/07/20

🚗 السيارة:
   • تويوتا كامري 2022
   • اللوحة: أ ب ج 1234

🛡️ التأمين:
   • التعاونية - تأمين شامل
   • الإجمالي: 3,305 ريال

هل كل شي صحيح وتبي نعتمد الطلب؟ ✅"
"""
    
    def _get_vehicle_summary(self, context: ConversationContext) -> str:
        from app.engine.vehicle_manager import VehicleManager
        
        manager_data = context.vehicle_data.get("manager", {})
        if not manager_data:
            return "لا توجد بيانات"
        
        vm = VehicleManager.from_dict(manager_data)
        if not vm.current_vehicle:
            return "لا توجد بيانات"
        
        v = vm.current_vehicle
        lines = []
        if v.brand and v.model:
            lines.append(f"• {v.brand} {v.model} {v.year or ''}")
        if v.plate_no:
            lines.append(f"• اللوحة: {v.plate_no}")
        if v.value:
            lines.append(f"• القيمة: {v.value:,} ريال")
        
        return "\n".join(lines) if lines else "لا توجد بيانات"
    
    def _get_profile_summary(self, context: ConversationContext) -> str:
        profile = context.profile_data
        lines = []
        
        if "national_id" in profile:
            masked = "****" + profile["national_id"][-4:]
            lines.append(f"• الهوية: {masked}")
        if "birth_date" in profile:
            lines.append(f"• الميلاد: {profile['birth_date']}")
        if "phone" in profile:
            lines.append(f"• الجوال: {profile['phone']}")
        
        return "\n".join(lines) if lines else "لا توجد بيانات"
    
    def _get_offer_summary(self, context: ConversationContext) -> str:
        offer = context.selected_offer or {}
        
        # 🔍 Logging: تسجيل العرض المختار
        company = offer.get('company', 'N/A')
        offer_id = offer.get('id', 'N/A')
        total_premium = offer.get("total_premium")
        price = offer.get("price")
        self.logger.info(f"📋 ORDER_SUMMARY - Selected offer: {company} (ID: {offer_id})")
        self.logger.info(f"   total_premium: {total_premium}")
        self.logger.info(f"   price: {price}")
        
        lines = []
        
        if offer.get("company"):
            lines.append(f"• الشركة: {offer['company']}")
        if offer.get("type"):
            lines.append(f"• نوع التغطية: {offer['type']}")
        
        # استخدام total_premium إذا كان موجوداً (من قاعدة البيانات)
        # أو price (من العروض الافتراضية) - كلاهما يحتوي على الضريبة
        total_price = offer.get("total_premium") or offer.get("price", 0)
        
        if total_price:
            # السعر النهائي (يحتوي بالفعل على الضريبة)
            total = float(total_price)
            
            # حساب السعر قبل الضريبة والضريبة للعرض فقط
            price_before_vat = total / 1.15
            vat = total - price_before_vat
            
            lines.append(f"• السعر قبل الضريبة: {price_before_vat:,.2f} ريال")
            lines.append(f"• الضريبة (15%): {vat:,.2f} ريال")
            lines.append(f"• الإجمالي: {total:,.2f} ريال")
        
        return "\n".join(lines) if lines else "لا توجد بيانات"
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة ملخص الطلب"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا أكد الطلب
        if intent == UserIntent.CONFIRM:
            self.logger.info("🧠 AI Transition: ORDER_SUMMARY -> FINAL_CONFIRMATION")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.FINAL_CONFIRMATION
            )
        
        # إذا أراد التعديل
        if intent == UserIntent.MODIFY:
            return StageResponse(
                should_transition=False,
                prompt_addition="\nاسأل العميل أي قسم يريد تعديله: البيانات الشخصية أم السيارة أم العرض؟"
            )
        
        return StageResponse(should_transition=False)


# Singleton instance
order_summary_stage = OrderSummaryStage()
