"""
Collecting Profile Stage - مرحلة جمع البيانات الشخصية (بعد اختيار العرض)
"""
from typing import Dict, Any, List
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from .base_stage import BaseStage, StageResponse


class CollectingProfileStage(BaseStage):
    """مرحلة جمع البيانات الشخصية"""
    
    stage = ConversationStage.COLLECTING_PROFILE
    order = 8
    name_ar = "بيانات العميل"
    
    def __init__(self):
        super().__init__()
        self.user_repo = None
        self._init_repo()
    
    def _init_repo(self):
        """تهيئة repository المستخدمين"""
        try:
            from app.db.repositories.user_repository import user_repository
            self.user_repo = user_repository
        except Exception as e:
            self.logger.warning(f"Could not init user repo: {e}")
    
    def get_stage_info(self) -> Dict[str, str]:
        return {
            "name": "جمع بيانات العميل",
            "description": "نحتاج: رقم الهوية، تاريخ الميلاد",
            "required_action": "اطلب البيانات بأسلوب ودي"
        }
    
    def get_required_fields(self) -> List[str]:
        """الحقول المطلوبة للبيانات الشخصية"""
        return ["national_id", "birth_date"]
    
    def get_collected_fields(self, context: ConversationContext) -> Dict[str, Any]:
        """الحقول المجمعة"""
        fields = {}
        if context.profile_data.get("national_id"):
            fields["national_id"] = context.profile_data["national_id"]
        if context.profile_data.get("birth_date"):
            fields["birth_date"] = context.profile_data["birth_date"]
        return fields
    
    def _get_short_summary(self, context: ConversationContext) -> str:
        """ملخص قصير للقائمة"""
        if context.profile_data.get("national_id"):
            masked = "****" + context.profile_data["national_id"][-4:]
            return f" ({masked})"
        return ""
    
    def get_prompt_instructions(self, context: ConversationContext) -> str:
        missing = self.get_missing_data(context)
        
        return f"""⚠️ أنت في مرحلة جمع بيانات العميل.

تعليمات مهمة:
1. في كل رد، اعرض للمستخدم قائمة البيانات المطلوبة
2. ضع ✅ أمام البيانات التي تم الحصول عليها
3. ضع ❌ أمام البيانات المطلوبة التي لم تُجمع بعد
4. استخدم إيموجي مناسبة 😊

📋 **قائمة البيانات:**
{missing}

⚠️ **مهم جداً:** يجب أن تعرض هذه القائمة للمستخدم في كل رد!

مثال على الرد:
"عشان نكمل الطلب، محتاج منك:

📋 **البيانات المطلوبة:**
✅ رقم الهوية: ****5432
❌ تاريخ الميلاد: مطلوب

ممكن تعطيني تاريخ ميلادك؟ 📅"
"""

    
    def get_missing_data(self, context: ConversationContext) -> str:
        """الحصول على البيانات الناقصة"""
        missing = []
        
        if "national_id" not in context.profile_data:
            missing.append("❌ رقم الهوية (مطلوب)")
        else:
            masked = "****" + context.profile_data["national_id"][-4:]
            missing.append(f"✅ رقم الهوية: {masked}")
            
        if "birth_date" not in context.profile_data:
            missing.append("❌ تاريخ الميلاد (مطلوب)")
        else:
            missing.append(f"✅ تاريخ الميلاد: {context.profile_data['birth_date']}")
        
        return "\n".join(missing)
    
    def handle_intent(
        self,
        intent,
        context: ConversationContext,
        extracted_data: Dict[str, Any]
    ) -> StageResponse:
        """معالجة النية في مرحلة جمع البيانات الشخصية"""
        
        # تحقق من اكتمال البيانات
        has_id = "national_id" in context.profile_data
        has_birth = "birth_date" in context.profile_data
        
        if has_id and has_birth:
            # حفظ المستخدم في DB
            self._save_user_to_db(context)
            
            # الانتقال لملخص الطلب (التدفق الجديد)
            self.logger.info("🧠 AI Transition: COLLECTING_PROFILE -> ORDER_SUMMARY")
            return StageResponse(
                should_transition=True,
                next_stage=ConversationStage.ORDER_SUMMARY
            )
        
        return StageResponse(should_transition=False)
    
    def _save_user_to_db(self, context: ConversationContext):
        """حفظ المستخدم في قاعدة البيانات"""
        if not self.user_repo:
            self.logger.warning("User repo not available")
            return
        
        try:
            # التحقق من عدم وجود المستخدم مسبقاً
            existing = self.user_repo.get_by_national_id(
                context.profile_data["national_id"]
            )
            
            if existing:
                context.user_id = str(existing["id"])
                self.logger.info(f"✅ Found existing user: {existing.get('user_code')}")
                return
            
            # إنشاء مستخدم جديد
            user = self.user_repo.create_user(
                national_id=context.profile_data["national_id"],
                birth_date=context.profile_data["birth_date"],
                phone=context.profile_data.get("phone")
            )
            
            if user and user.get("id"):
                context.user_id = str(user["id"])
                self.logger.info(f"✅ Saved user to DB: {user.get('user_code')}")
                
        except Exception as e:
            self.logger.error(f"Error saving user: {e}")


# Singleton instance
collecting_profile_stage = CollectingProfileStage()
