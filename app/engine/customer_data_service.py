"""
Customer Data Service - خدمة إدارة بيانات العملاء الاحترافية

تتعامل مع:
1. حفظ مسودات البيانات (حتى عند الإلغاء)
2. استرجاع البيانات تلقائياً
3. سجل العميل الكامل
4. تتبع التفاعلات
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CustomerDataService:
    """خدمة إدارة بيانات العملاء"""
    
    def __init__(self):
        self.mongodb = None
        self._init_mongodb()
    
    def _init_mongodb(self):
        """تهيئة الاتصال بـ MongoDB"""
        try:
            from app.db.mongodb import mongodb_manager
            self.mongodb = mongodb_manager
        except Exception as e:
            logger.warning(f"Could not init MongoDB: {e}")
    
    async def save_customer_draft(
        self,
        phone: str,
        profile_data: Dict[str, Any],
        vehicle_data: Dict[str, Any],
        last_stage: str,
        status: str = "draft",  # draft, cancelled, expired
        selected_service: Optional[str] = None,
        selected_offer: Optional[Dict] = None,
        reason: Optional[str] = None
    ) -> bool:
        """
        حفظ مسودة بيانات العميل
        تُستخدم عند الإلغاء أو الخروج لحفظ التقدم
        """
        if not self.mongodb or not self.mongodb.is_connected():
            logger.warning("MongoDB not connected - cannot save draft")
            return False
        
        try:
            draft = {
                "phone": phone,
                "national_id": profile_data.get("national_id"),
                "profile_data": profile_data,
                "vehicle_data": vehicle_data,
                "selected_service": selected_service,
                "selected_offer": selected_offer,
                "last_stage": last_stage,
                "status": status,
                "reason": reason,
                "updated_at": datetime.now(),
            }
            
            # Upsert: تحديث إذا موجود، إنشاء إذا جديد
            result = await self.mongodb.db.customer_drafts.update_one(
                {"phone": phone},
                {
                    "$set": draft,
                    "$setOnInsert": {"created_at": datetime.now()}
                },
                upsert=True
            )
            
            logger.info(f"✅ Saved customer draft for phone: {phone[-4:]}, status: {status}")
            
            # تسجيل التفاعل في السجل
            await self._log_interaction(phone, "draft_saved", {
                "stage": last_stage,
                "status": status,
                "reason": reason
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving customer draft: {e}")
            return False
    
    async def get_customer_draft(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        استرجاع مسودة بيانات العميل
        تُستخدم عند بداية محادثة جديدة
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return None
        
        try:
            draft = await self.mongodb.db.customer_drafts.find_one(
                {"phone": phone}
            )
            
            if draft:
                draft["_id"] = str(draft["_id"])
                logger.info(f"📋 Found draft for phone: {phone[-4:]}, stage: {draft.get('last_stage')}")
            
            return draft
            
        except Exception as e:
            logger.error(f"Error getting customer draft: {e}")
            return None
    
    async def get_customer_by_national_id(self, national_id: str) -> Optional[Dict[str, Any]]:
        """
        جلب بيانات العميل برقم الهوية
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return None
        
        try:
            # البحث في المسودات
            draft = await self.mongodb.db.customer_drafts.find_one(
                {"national_id": national_id}
            )
            
            # البحث في المستخدمين المسجلين
            from app.db.mongodb import find_user_by_national_id
            user = await find_user_by_national_id(national_id)
            
            return {
                "draft": draft,
                "user": user,
                "has_data": bool(draft or user)
            }
            
        except Exception as e:
            logger.error(f"Error getting customer by national_id: {e}")
            return None
    
    async def get_full_customer_history(self, phone: str = None, national_id: str = None) -> Dict[str, Any]:
        """
        جلب السجل الكامل للعميل
        يشمل: المسودات، الوثائق، الطلبات، المحادثات
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return {"error": "Database not connected"}
        
        try:
            result = {
                "phone": phone,
                "national_id": national_id,
                "draft": None,
                "user_profile": None,
                "policies": [],
                "orders": [],
                "vehicles": [],
                "interactions": [],
                "conversation_count": 0
            }
            
            # 1. جلب المسودة
            if phone:
                result["draft"] = await self.get_customer_draft(phone)
            
            # 2. جلب بيانات المستخدم من MongoDB
            if national_id:
                from app.db.mongodb import find_user_by_national_id, get_user_policies
                user = await find_user_by_national_id(national_id)
                if user:
                    result["user_profile"] = user
                    result["policies"] = await get_user_policies(national_id)
            elif phone:
                from app.db.mongodb import find_user_by_phone
                user = await find_user_by_phone(phone)
                if user:
                    result["user_profile"] = user
                    national_id = user.get("national_id")
                    if national_id:
                        from app.db.mongodb import get_user_policies
                        result["policies"] = await get_user_policies(national_id)
            
            # 3. جلب التفاعلات
            if phone:
                interactions = await self.mongodb.db.customer_interactions.find(
                    {"phone": phone}
                ).sort("timestamp", -1).limit(50).to_list(length=50)
                result["interactions"] = interactions
            
            # 4. عدد المحادثات
            if phone or national_id:
                query = {}
                if phone:
                    query["phone"] = phone
                count = await self.mongodb.db.conversation_contexts.count_documents(query)
                result["conversation_count"] = count
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting full customer history: {e}")
            return {"error": str(e)}
    
    async def restore_context_from_draft(self, context, phone: str) -> bool:
        """
        استعادة السياق من المسودة المحفوظة
        تُستخدم عند بداية محادثة جديدة لتوفير وقت العميل
        """
        try:
            draft = await self.get_customer_draft(phone)
            
            if not draft:
                return False
            
            # استعادة البيانات الشخصية
            if draft.get("profile_data"):
                for key, value in draft["profile_data"].items():
                    if value and key not in context.profile_data:
                        context.profile_data[key] = value
            
            # استعادة بيانات السيارة
            if draft.get("vehicle_data"):
                if not context.vehicle_data.get("manager"):
                    context.vehicle_data = draft["vehicle_data"]
            
            # استعادة الخدمة المختارة
            if draft.get("selected_service"):
                if "service_type" not in context.profile_data:
                    context.profile_data["service_type"] = draft["selected_service"]
            
            logger.info(f"✅ Restored context from draft for phone: {phone[-4:]}")
            
            # تسجيل التفاعل
            await self._log_interaction(phone, "draft_restored", {
                "from_stage": draft.get("last_stage"),
                "to_stage": context.current_stage.value
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error restoring context from draft: {e}")
            return False
    
    async def _log_interaction(self, phone: str, action: str, details: Dict[str, Any] = None):
        """
        تسجيل تفاعل في سجل العميل
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return
        
        try:
            interaction = {
                "phone": phone,
                "action": action,
                "details": details or {},
                "timestamp": datetime.now()
            }
            
            await self.mongodb.db.customer_interactions.insert_one(interaction)
            
        except Exception as e:
            logger.error(f"Error logging interaction: {e}")
    
    async def update_draft_status(self, phone: str, status: str, reason: Optional[str] = None) -> bool:
        """
        تحديث حالة المسودة
        الحالات: draft, cancelled, completed, expired
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return False
        
        try:
            result = await self.mongodb.db.customer_drafts.update_one(
                {"phone": phone},
                {
                    "$set": {
                        "status": status,
                        "reason": reason,
                        "updated_at": datetime.now()
                    }
                }
            )
            
            if result.modified_count > 0:
                logger.info(f"✅ Updated draft status for {phone[-4:]}: {status}")
                await self._log_interaction(phone, f"status_changed_to_{status}", {"reason": reason})
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating draft status: {e}")
            return False
    
    async def delete_draft(self, phone: str) -> bool:
        """
        حذف مسودة (عند اكتمال الطلب بنجاح)
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return False
        
        try:
            result = await self.mongodb.db.customer_drafts.delete_one({"phone": phone})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Deleted draft for phone: {phone[-4:]}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting draft: {e}")
            return False
    
    async def get_resumable_sessions(self, phone: str) -> List[Dict[str, Any]]:
        """
        جلب الجلسات القابلة للاستئناف
        """
        if not self.mongodb or not self.mongodb.is_connected():
            return []
        
        try:
            # جلب المسودات غير المكتملة
            drafts = await self.mongodb.db.customer_drafts.find({
                "phone": phone,
                "status": {"$in": ["draft", "cancelled"]}
            }).sort("updated_at", -1).limit(5).to_list(length=5)
            
            return drafts
            
        except Exception as e:
            logger.error(f"Error getting resumable sessions: {e}")
            return []


# Global instance
customer_data_service = CustomerDataService()
