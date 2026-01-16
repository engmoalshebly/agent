"""
Confirming Vehicle Stage - مرحلة تأكيد بيانات السيارة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class ConfirmingVehicleStage(BaseStage):
    """مرحلة تأكيد بيانات السيارة قبل عرض الأسعار"""
    
    stage = ConversationStage.CONFIRMING_VEHICLE
    order = 4
    name_ar = "تأكيد السيارة"
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "تأكيد بيانات السيارة",
            "description": "عرض بيانات السيارة والتأكد من صحتها",
            "required_action": "اعرض البيانات واسأل العميل هل نعتمدها"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة: تأكيد السيارة"""
        return ["vehicle_confirmed"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        return {}
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        from app.engine.vehicle_manager import VehicleManager
        
        # جلب بيانات السيارة
        vehicle_info = self._get_vehicle_summary(context)
        
        return f"""⚠️ أنت في مرحلة تأكيد بيانات السيارة.

📋 بيانات السيارة المدخلة:
{vehicle_info}

تعليمات مهمة:
- اعرض البيانات بشكل مرتب وواضح
- اسأل العميل: "هل البيانات صحيحة وتبي نعتمدها؟ ✅"
- إذا أراد التعديل، اسأله أي بيان يريد تغييره

مثال على الرد:
"حلو! 👍 خليني أتأكد معك من بيانات السيارة:

🚗 السيارة: تويوتا كامري 2022
💰 القيمة: 85,000 ريال
🔢 اللوحة: أ ب ج 1234

هل البيانات صحيحة وتبي نعتمدها؟ ✅
أو تبي تعدل شي؟"
"""
    
    def _get_vehicle_summary(self, context: ConversationContext) -> str:
        """الحصول على ملخص بيانات السيارة"""
        from app.engine.vehicle_manager import VehicleManager
        
        manager_data = context.vehicle_data.get("manager", {})
        if not manager_data:
            return "لا توجد بيانات"
        
        vm = VehicleManager.from_dict(manager_data)
        if not vm.current_vehicle:
            return "لا توجد بيانات"
        
        v = vm.current_vehicle
        lines = []
        if v.brand:
            lines.append(f"🚗 النوع: {v.brand}")
        if v.model:
            lines.append(f"📝 الموديل: {v.model}")
        if v.year:
            lines.append(f"📅 السنة: {v.year}")
        if v.value:
            lines.append(f"💰 القيمة: {v.value:,} ريال")
        if v.plate_no:
            lines.append(f"🔢 اللوحة: {v.plate_no}")
        
        return "\n".join(lines) if lines else "لا توجد بيانات"
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة تأكيد بيانات السيارة"""
        from app.engine.ai_intent_analyzer import UserIntent
        
        # إذا أكد البيانات
        if intent == UserIntent.CONFIRM:
            # حفظ السيارة في DB
            self._save_vehicle_to_db(context)
            
            # 🆕 جلب العروض فوراً من قاعدة البيانات
            offers = self._fetch_offers_immediately(context)
            offers_text = self._format_offers(offers)
            
            # حفظ العروض في السياق
            context.offers_shown = offers
            
            self.logger.info(f"🧠 AI Transition: CONFIRMING_VEHICLE -> SHOWING_OFFERS (fetched {len(offers)} offers)")
            
            # إرجاع الرد مع العروض مباشرة
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.SHOWING_OFFERS,
                special_response=f"""ممتاز! ✅ تم اعتماد بيانات السيارة.

🔍 دورت لك على أفضل العروض المتوفرة:

{offers_text}

أي عرض يناسبك؟ 🤔"""
            )
        
        # إذا أراد التعديل
        if intent == UserIntent.MODIFY:
            self.logger.info("🧠 AI Transition: CONFIRMING_VEHICLE -> COLLECTING_VEHICLE (تعديل)")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.COLLECTING_VEHICLE
            )
        
        return StageResponse(should_transition=False)
    
    def _fetch_offers_immediately(self, context: ConversationContext) -> List[Dict]:
        """
        جلب العروض فوراً من قاعدة البيانات
        بناءً على بيانات السيارة
        """
        try:
            from app.engine.vehicle_manager import VehicleManager
            from app.engine.sql_engine import insurance_sql_engine
            
            # جلب قيمة السيارة
            vehicle_value = 0
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle and vm.current_vehicle.value:
                    vehicle_value = vm.current_vehicle.value
            
            # محاولة جلب العروض من DB
            try:
                result = insurance_sql_engine._execute_sql(
                    "SELECT * FROM offers WHERE is_active = true ORDER BY price ASC LIMIT 5"
                )
                if result and result.get("data") and len(result["data"]) > 0:
                    self.logger.info(f"✅ Fetched {len(result['data'])} offers from DB")
                    return result["data"]
            except Exception as e:
                self.logger.warning(f"Could not fetch from DB: {e}")
            
            # العروض الافتراضية بناءً على قيمة السيارة
            base_price = max(vehicle_value * 0.03, 1500)
            
            return [
                {
                    "id": 1,
                    "company": "التعاونية",
                    "type": "شامل",
                    "price": round(base_price * 1.1),
                    "features": ["تغطية شاملة", "سيارة بديلة 7 أيام", "مساعدة على الطريق"],
                    "rating": 4.5
                },
                {
                    "id": 2,
                    "company": "الراجحي",
                    "type": "شامل",
                    "price": round(base_price * 1.05),
                    "features": ["تغطية شاملة", "سيارة بديلة 5 أيام", "خصم تجديد"],
                    "rating": 4.3
                },
                {
                    "id": 3,
                    "company": "ملاذ",
                    "type": "طرف ثالث بلس",
                    "price": round(base_price * 0.6),
                    "features": ["تغطية ضد الغير", "سرقة وحريق", "سعر مميز"],
                    "rating": 4.0
                }
            ]
        except Exception as e:
            self.logger.error(f"Error fetching offers: {e}")
            return []
    
    def _format_offers(self, offers: List[Dict]) -> str:
        """تنسيق العروض للعرض"""
        if not offers:
            return "عذراً، لا توجد عروض متوفرة حالياً."
        
        lines = []
        for i, offer in enumerate(offers, 1):
            company = offer.get("company", "شركة")
            type_ = offer.get("type", "تأمين")
            price = offer.get("price", 0)
            features = offer.get("features", [])
            
            lines.append(f"🏢 **العرض {i}: {company}**")
            lines.append(f"   • النوع: {type_}")
            lines.append(f"   • السعر: {price:,} ريال")
            if features:
                lines.append(f"   • المميزات: {', '.join(features[:3])}")
            lines.append("")
        
        return "\n".join(lines)
    
    def _save_vehicle_to_db(self, context: ConversationContext):
        """حفظ السيارة في قاعدة البيانات"""
        from app.engine.vehicle_manager import VehicleManager
        
        try:
            from app.db.repositories.vehicle_repository import vehicle_repository
            
            manager_data = context.vehicle_data.get("manager", {})
            if not manager_data or not context.user_id:
                return
            
            vm = VehicleManager.from_dict(manager_data)
            v = vm.current_vehicle
            if not v:
                return
            
            saved = vehicle_repository.create_vehicle(
                user_id=int(context.user_id),
                plate_no=v.plate_no or "",
                brand=v.brand or "",
                model=v.model or "",
                model_year=v.year or 2024,
                vehicle_value=v.value or 0
            )
            if saved and saved.get("id"):
                context.vehicle_data["db_id"] = saved["id"]
                self.logger.info(f"✅ Saved vehicle to DB: {saved.get('plate_no')}")
        except Exception as e:
            self.logger.error(f"Error saving vehicle: {e}")


# Singleton instance
confirming_vehicle_stage = ConfirmingVehicleStage()
