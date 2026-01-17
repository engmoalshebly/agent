"""
Collecting Vehicle Stage - مرحلة جمع بيانات السيارة
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class CollectingVehicleStage(BaseStage):
    """مرحلة جمع بيانات السيارة"""
    
    stage = ConversationStage.COLLECTING_VEHICLE
    order = 3
    name_ar = "بيانات السيارة"
    
    def __init__(self):
        super().__init__()
        self.vehicle_repo = None
        self._init_repo()
    
    def _init_repo(self):
        """تهيئة repository السيارات"""
        try:
            from app.db.repositories.vehicle_repository import vehicle_repository
            self.vehicle_repo = vehicle_repository
        except Exception as e:
            self.logger.warning(f"Could not init vehicle repo: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "جمع بيانات السيارة",
            "description": "نحتاج: نوع السيارة، موديلها، سنتها، قيمتها، رقم اللوحة",
            "required_action": "اجمع بيانات السيارة بالترتيب"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة لبيانات السيارة"""
        return ["vehicle_brand", "vehicle_model", "vehicle_year", "vehicle_value", "plate_no"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة من بيانات السيارة"""
        from app.engine.vehicle_manager import VehicleManager
        
        fields = {}
        manager_data = context.vehicle_data.get("manager", {})
        
        if manager_data:
            try:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle:
                    v = vm.current_vehicle
                    if v.brand:
                        fields["vehicle_brand"] = v.brand
                    if v.model:
                        fields["vehicle_model"] = v.model
                    if v.year:
                        fields["vehicle_year"] = v.year
                    if v.value:
                        fields["vehicle_value"] = v.value
                    if v.plate_no:
                        fields["plate_no"] = v.plate_no
            except Exception:
                pass
        
        return fields
    
    def _get_short_summary(self, context: ConversationContext) -> str:
        """ملخص قصير للقائمة"""
        fields = self.get_collected_fields(context)
        brand = fields.get("vehicle_brand", "")
        model = fields.get("vehicle_model", "")
        return f" ({brand} {model})" if brand and model else ""
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        missing = self.get_missing_data(context)
        return f"""⚠️ أنت في مرحلة جمع بيانات السيارة.

⛔ **ممنوع منعاً باتاً:**
- لا تطلب الرقم التسلسلي (VIN) أبداً
- لا تطلب رقم الهيكل أبداً
- لا تطلب نوع السيارة (سيدان/دفع رباعي) أبداً
- لا تطلب أي بيانات غير موجودة في القائمة أدناه

✅ **البيانات المطلوبة فقط (5 حقول):**
1. نوع/ماركة السيارة (مثل: تويوتا، هيونداي)
2. موديل السيارة (مثل: كامري، سوناتا)
3. سنة الصنع (مثل: 2022)
4. القيمة التقديرية بالريال (مثل: 80000)
5. رقم اللوحة (مثل: أ ب ج 1234)

📋 **حالة البيانات الحالية:**
{missing}

⚠️ **تعليمات إلزامية:**
1. اعرض القائمة أعلاه للمستخدم في كل رد
2. ضع ✅ أمام البيانات المكتملة
3. ضع ❌ أمام البيانات الناقصة
4. اسأل عن الحقل الناقص التالي فقط

📝 **مثال على الرد الصحيح:**
"تمام! 😊 هذي بيانات السيارة:

📋 **بيانات السيارة:**
✅ النوع: هيونداي
✅ الموديل: سوناتا
✅ السنة: 2021
❌ القيمة: مطلوب
❌ اللوحة: مطلوب

كم القيمة التقديرية للسيارة؟ 💰"
"""


    
    def get_missing_data(self, context: ConversationContext) -> str:
        """الحصول على البيانات الناقصة للسيارة"""
        from app.engine.vehicle_manager import VehicleManager
        
        missing = []
        manager_data = context.vehicle_data.get("manager", {})
        
        if manager_data:
            vm = VehicleManager.from_dict(manager_data)
            if vm.current_vehicle:
                v = vm.current_vehicle
                if not v.brand:
                    missing.append("❌ نوع السيارة (مطلوب)")
                else:
                    missing.append(f"✅ نوع السيارة: {v.brand}")
                    
                if not v.model:
                    missing.append("❌ موديل السيارة (مطلوب)")
                else:
                    missing.append(f"✅ الموديل: {v.model}")
                    
                if not v.year:
                    missing.append("❌ سنة الصنع (مطلوب)")
                else:
                    missing.append(f"✅ السنة: {v.year}")
                    
                if not v.value:
                    missing.append("❌ القيمة التقديرية (مطلوب)")
                else:
                    missing.append(f"✅ القيمة: {v.value:,} ريال")
                    
                if not v.plate_no:
                    missing.append("❌ رقم اللوحة (مطلوب)")
                else:
                    missing.append(f"✅ اللوحة: {v.plate_no}")
        
        return "\n".join(missing) if missing else "لم تُحدد بيانات السيارة بعد"
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة جمع بيانات السيارة"""
        from app.engine.vehicle_manager import VehicleManager
        
        manager_data = context.vehicle_data.get("manager", {})
        if not manager_data:
            return StageResponse(should_transition=False)
        
        vm = VehicleManager.from_dict(manager_data)
        v = vm.current_vehicle
        
        if v and v.is_complete:
            # ✅ بيانات السيارة اكتملت - الانتقال لمرحلة التأكيد
            self.logger.info("🧠 AI Transition: COLLECTING_VEHICLE -> CONFIRMING_VEHICLE")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.CONFIRMING_VEHICLE,
                # إضافة البيانات للتأكيد
                extracted_data={
                    "vehicle_summary": self._format_vehicle_summary(v),
                    "vehicle_complete": True
                }
            )
        
        return StageResponse(should_transition=False)
    
    def _format_vehicle_summary(self, vehicle) -> str:
        """تنسيق ملخص بيانات السيارة للتأكيد"""
        return f"""🚗 السيارة: {vehicle.brand} {vehicle.model}
📅 السنة: {vehicle.year}
💰 القيمة: {vehicle.value:,} ريال
🔢 اللوحة: {vehicle.plate_no}"""
    
    def _save_vehicle_to_db(self, context: ConversationContext, vehicle):
        """حفظ السيارة في قاعدة البيانات"""
        if not self.vehicle_repo or not context.user_id:
            return
        
        try:
            saved = self.vehicle_repo.create_vehicle(
                user_id=int(context.user_id),
                plate_no=vehicle.plate_no or "",
                brand=vehicle.brand or "",
                model=vehicle.model or "",
                model_year=vehicle.year or 2024,
                vehicle_value=vehicle.value or 0
            )
            if saved and saved.get("id"):
                context.vehicle_data["db_id"] = saved["id"]
                self.logger.info(f"✅ Saved vehicle to DB: {saved.get('plate_no')}")
        except Exception as e:
            self.logger.error(f"Error saving vehicle: {e}")


# Singleton instance
collecting_vehicle_stage = CollectingVehicleStage()
