"""
SAIA Insurance Broker Platform - Stage Transitions Module
إدارة الانتقال بين المراحل
"""
from typing import Dict, Any, Optional
import logging
import re

from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext
from app.engine.vehicle_manager import VehicleManager

logger = logging.getLogger(__name__)


class StageTransitionManager:
    """
    مدير الانتقال بين المراحل
    يتعامل مع:
    - الانتقالات التلقائية عند اكتمال البيانات
    - نوايا التعديل والإلغاء
    - الانتقالات القائمة على نية المستخدم
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def update_context_with_data(
        self,
        context: ConversationContext,
        data: Dict[str, Any]
    ):
        """
        تحديث السياق بالبيانات المستخرجة
        """
        # تحديث بيانات الملف الشخصي
        if "national_id" in data and "national_id" not in context.profile_data:
            context.profile_data["national_id"] = data["national_id"]
        
        if "phone" in data and "phone" not in context.profile_data:
            context.profile_data["phone"] = data["phone"]
        
        if "date" in data and "birth_date" not in context.profile_data:
            context.profile_data["birth_date"] = data["date"]
        
        if "birth_date" in data and "birth_date" not in context.profile_data:
            context.profile_data["birth_date"] = data["birth_date"]
        
        # تحديث بيانات السيارة
        self._update_vehicle_data(context, data)
    
    def _update_vehicle_data(
        self,
        context: ConversationContext,
        data: Dict[str, Any]
    ):
        """
        تحديث بيانات السيارة في VehicleManager
        مع تحويل الأنواع المناسبة
        """
        # التحقق من وجود بيانات سيارة
        vehicle_fields = ["brand", "model", "year", "price", "plate_no"]
        has_vehicle_data = any(f in data for f in vehicle_fields)
        
        if not has_vehicle_data:
            return
        
        # الحصول على VehicleManager أو إنشائه
        manager_data = context.vehicle_data.get("manager", {})
        if manager_data:
            vm = VehicleManager.from_dict(manager_data)
        else:
            vm = VehicleManager(context.conversation_id)
            vm.start_new_vehicle()
        
        # تحويل وتحديث البيانات
        update_kwargs = {}
        
        if "brand" in data:
            update_kwargs["brand"] = data["brand"]
        
        if "model" in data:
            update_kwargs["model"] = data["model"]
        
        if "year" in data:
            try:
                update_kwargs["year"] = int(data["year"])
            except (ValueError, TypeError):
                pass
        
        if "price" in data:
            try:
                price_str = str(data["price"]).replace(",", "").replace(" ", "")
                update_kwargs["value"] = float(price_str)
            except (ValueError, TypeError):
                pass
        
        if "plate_no" in data:
            update_kwargs["plate_no"] = data["plate_no"]
        
        # تحديث السيارة
        if update_kwargs:
            vm.update_current(**update_kwargs)
            context.vehicle_data["manager"] = vm.to_dict()
            self.logger.info(f"🚗 Updated vehicle data: {list(update_kwargs.keys())}")
    
    def determine_transition(
        self,
        context: ConversationContext,
        message: str,
        extracted_data: Dict[str, Any],
        ai_intent_result=None
    ) -> bool:
        """
        تحديد الانتقال بين المراحل
        Returns: True إذا تم الانتقال
        """
        # أولاً: التحقق من النوايا الخاصة (إلغاء، تعديل، رجوع)
        if self._handle_special_intents(context, message, extracted_data):
            return True
        
        # ثانياً: استخدام AI Intent إذا متوفر
        if ai_intent_result:
            return self._handle_ai_intent_transition(
                context, message, extracted_data, ai_intent_result
            )
        
        # ثالثاً: الانتقالات التلقائية عند اكتمال البيانات
        return self._handle_auto_transition(context, message, extracted_data)
    
    def _handle_special_intents(
        self,
        context: ConversationContext,
        message: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        معالجة النوايا الخاصة: إلغاء، تعديل، رجوع، طلب جديد
        """
        # === طلب تأمين جديد (إعادة تهيئة) ===
        new_request_words = [
            "تأمين جديد", "طلب جديد", "سيارة ثانية", "سيارة أخرى",
            "من البداية", "ابدأ من جديد", "طلب آخر", "تأمين ثاني",
            "نبدأ من الصفر", "سيارة ثانيه"
        ]
        if any(w in message for w in new_request_words):
            self._reset_for_new_request(context)  # يحافظ على الهوية
            return True
        
        # === إعادة تهيئة بعد اكتمال الطلب ===
        completed_stages = [
            ConversationStage.INVOICE_ISSUED,
            ConversationStage.CONFIRMATION,
        ]
        if context.current_stage in completed_stages:
            # إذا طلب المستخدم أي شيء جديد بعد اكتمال الطلب
            if any(w in message for w in ["تأمين", "سيارة", "عرض", "نعم"]):
                self._reset_context(context)
                self.logger.info("🔄 Session reset after completion")
                return True
        
        # إذا في ORDER_SUMMARY والمستخدم أكد وتم إصدار الوثيقة
        if context.current_stage == ConversationStage.ORDER_SUMMARY:
            if data.get("confirmation"):
                # إعادة تهيئة للطلب الجديد مع الحفاظ على البيانات الشخصية
                self._reset_for_new_request(context)
                return True
        
        # نية الإلغاء - كلمات أكثر تحديداً لتجنب التطابق الخاطئ
        # مثال: "الغي" تتطابق خطأً مع "ضد الغير"
        cancel_phrases = [
            "الغي الطلب", "الغاء الطلب", "لا اريد التأمين", "ما ابي تأمين",
            "خلاص لا اريد", "الغيها كلها", "ابي الغي", "ابغى الغي"
        ]
        if any(p in message for p in cancel_phrases):
            if context.pending_action == "confirm_cancel" and data.get("confirmation"):
                self._reset_context(context)
                return True
            else:
                context.pending_action = "confirm_cancel"
                return True
        
        # إذا كان هناك إجراء معلق ينتظر التأكيد
        if context.pending_action == "confirm_cancel":
            if data.get("confirmation"):
                self._reset_context(context)
                context.pending_action = None
                return True  # فقط عند إجراء فعلي
            context.pending_action = None
            # لا نُرجع True هنا - ندع الانتقال الطبيعي يحدث
        
        # نية التعديل - كلمات أكثر تحديداً لتجنب التطابق الخاطئ
        # مثال: "غير" تتطابق خطأً مع "ضد الغير"
        modify_phrases = [
            "غير الخدمة", "غير النوع", "غير التأمين", "عدل البيانات",
            "تغيير الخدمة", "تغيير النوع", "تصحيح البيانات", "اعدل",
            "ابي اغير", "ابغى اغير", "اريد تغيير"
        ]
        if any(p in message for p in modify_phrases):
            return self._handle_modify_intent(context, message)
        
        # نية الاستكمال
        resume_words = ["اكمل", "نكمل", "استمر", "كمل"]
        if any(w in message for w in resume_words):
            if context.current_stage == ConversationStage.GREETING:
                return self._handle_resume_intent(context)
        
        return False
    
    def _handle_modify_intent(self, context: ConversationContext, message: str) -> bool:
        """معالجة نية التعديل"""
        if any(w in message for w in ["هوية", "الهوية"]):
            context.profile_data.pop("national_id", None)
            context.current_stage = ConversationStage.COLLECTING_PROFILE
            context.last_question = "national_id"
            return True
        
        if any(w in message for w in ["ميلاد", "الميلاد"]):
            context.profile_data.pop("birth_date", None)
            context.current_stage = ConversationStage.COLLECTING_PROFILE
            context.last_question = "birth_date"
            return True
        
        if any(w in message for w in ["سيارة", "السيارة", "اللوحة"]):
            context.current_stage = ConversationStage.COLLECTING_VEHICLE
            return True
        
        if any(w in message for w in ["تأمين", "التأمين", "عرض", "العرض", "شركة"]):
            context.current_stage = ConversationStage.SHOWING_OFFERS
            context.selected_offer = None
            return True
        
        return False
    
    def _handle_resume_intent(self, context: ConversationContext) -> bool:
        """معالجة نية الاستكمال"""
        if context.profile_data and "national_id" in context.profile_data:
            if context.selected_offer:
                context.current_stage = ConversationStage.PENDING_PAYMENT
            elif context.offers_shown:
                context.current_stage = ConversationStage.AWAITING_SELECTION
            elif "manager" in context.vehicle_data:
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
            else:
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
            return True
        return False
    
    def _handle_auto_transition(
        self,
        context: ConversationContext,
        message: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        الانتقالات التلقائية عند اكتمال البيانات
        """
        stage = context.current_stage
        
        # GREETING -> SELECTING_SERVICE
        if stage == ConversationStage.GREETING:
            if data.get("choice") == 1 or any(
                w in message for w in ["تأمين", "جديد", "سيارة", "أبي", "ابي", "اريد", "أريد"]
            ):
                context.current_stage = ConversationStage.SELECTING_SERVICE
                return True
        
        # SELECTING_SERVICE -> CONFIRMING_VEHICLE (عند اكتمال بيانات السيارة)
        # التأكيد أولاً ثم العروض
        elif stage == ConversationStage.SELECTING_SERVICE:
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle and vm.current_vehicle.is_complete:
                    # تأكد من وجود نوع الخدمة أو ضعها افتراضياً
                    if "service_type" not in context.profile_data:
                        context.profile_data["service_type"] = "comprehensive"
                    # الانتقال لمرحلة التأكيد
                    context.current_stage = ConversationStage.CONFIRMING_VEHICLE
                    self.logger.info("🔄 Auto-transition: SELECTING_SERVICE -> CONFIRMING_VEHICLE")
                    return True
        
        # COLLECTING_PROFILE -> ORDER_SUMMARY (عند اكتمال البيانات)
        elif stage == ConversationStage.COLLECTING_PROFILE:
            has_id = "national_id" in context.profile_data
            has_birth = "birth_date" in context.profile_data
            
            if has_id and has_birth:
                context.current_stage = ConversationStage.ORDER_SUMMARY
                self.logger.info("🔄 Auto-transition: COLLECTING_PROFILE -> ORDER_SUMMARY")
                return True
        
        # COLLECTING_VEHICLE -> CONFIRMING_VEHICLE (تأكيد بيانات السيارة)
        elif stage == ConversationStage.COLLECTING_VEHICLE:
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle and vm.current_vehicle.is_complete:
                    # الانتقال لمرحلة التأكيد
                    context.current_stage = ConversationStage.CONFIRMING_VEHICLE
                    self.logger.info("🔄 Auto-transition: COLLECTING_VEHICLE -> CONFIRMING_VEHICLE")
                    return True
        
        # CONFIRMING_VEHICLE -> SHOWING_OFFERS (عند التأكيد بواسطة AI)
        elif stage == ConversationStage.CONFIRMING_VEHICLE:
            # استخدام تحليل AI لكشف التأكيد
            is_confirmed = data.get("confirmation", False)
            
            if is_confirmed:
                # جلب العروض مباشرة
                self._fetch_and_save_offers(context)
                context.current_stage = ConversationStage.SHOWING_OFFERS
                self.logger.info("🔄 Auto-transition: CONFIRMING_VEHICLE -> SHOWING_OFFERS (AI confirmed)")
                return True
        
        # OFFER_DETAILS -> COLLECTING_PROFILE (عند التأكيد بواسطة AI)
        elif stage == ConversationStage.OFFER_DETAILS:
            is_confirmed = data.get("confirmation", False)
            
            if is_confirmed:
                context.current_stage = ConversationStage.COLLECTING_PROFILE
                self.logger.info("🔄 Auto-transition: OFFER_DETAILS -> COLLECTING_PROFILE (AI confirmed)")
                return True
        
        # SHOWING_OFFERS -> OFFER_DETAILS (عند اختيار العرض بواسطة AI)
        elif stage == ConversationStage.SHOWING_OFFERS:
            # استخدام تحليل AI لكشف اختيار العرض
            company_name = data.get("company_name", "")
            offer_number = data.get("offer_number")
            
            selected_offer = None
            
            # كشف اختيار بالرقم من AI
            if offer_number and context.offers_shown:
                try:
                    idx = int(offer_number) - 1
                    if 0 <= idx < len(context.offers_shown):
                        selected_offer = context.offers_shown[idx]
                except (ValueError, IndexError):
                    pass
            
            # كشف اختيار باسم الشركة من AI
            if selected_offer is None and company_name and context.offers_shown:
                company_lower = company_name.lower()
                for offer in context.offers_shown:
                    offer_company = offer.get("company", "").lower()
                    if company_lower in offer_company or offer_company in company_lower:
                        selected_offer = offer
                        break
            
            if selected_offer:
                context.selected_offer = selected_offer
                # الانتقال إلى OFFER_DETAILS لعرض تفاصيل العرض الكاملة
                context.current_stage = ConversationStage.OFFER_DETAILS
                self.logger.info(f"🔄 Auto-transition: SHOWING_OFFERS -> OFFER_DETAILS (AI selected: {selected_offer.get('company')})")
                return True
        
        return False
    
    def _handle_ai_intent_transition(
        self,
        context: ConversationContext,
        message: str,
        extracted_data: Dict[str, Any],
        ai_result
    ) -> bool:
        """
        الانتقال بناءً على تحليل نية المستخدم بالـ AI
        """
        from app.engine.ai_intent_analyzer import UserIntent
        
        stage = context.current_stage
        intent = ai_result.intent
        
        # GREETING -> SELECTING_SERVICE or COLLECTING_VEHICLE
        if stage == ConversationStage.GREETING:
            # إذا استخرج الـ AI نوع الخدمة، ننتقل مباشرة لجمع بيانات السيارة
            service_type = ai_result.extracted_data.get("service_type")
            if service_type:
                context.profile_data["service_type"] = service_type
                # تهيئة VehicleManager
                if "manager" not in context.vehicle_data:
                    vm = VehicleManager(context.conversation_id)
                    vm.start_new_vehicle()
                    context.vehicle_data["manager"] = vm.to_dict()
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
                self.logger.info(f"🧠 AI Transition: GREETING -> COLLECTING_VEHICLE (service: {service_type})")
                return True
            # إذا طلب خدمة بدون تحديد نوع
            if intent in (UserIntent.ASK_SERVICES, UserIntent.SELECT_SERVICE):
                context.current_stage = ConversationStage.SELECTING_SERVICE
                self.logger.info("🧠 AI Transition: GREETING -> SELECTING_SERVICE")
                return True
        
        # SELECTING_SERVICE -> COLLECTING_VEHICLE
        elif stage == ConversationStage.SELECTING_SERVICE:
            if intent == UserIntent.SELECT_SERVICE:
                service_type = ai_result.extracted_data.get("service_type")
                service_name = ai_result.extracted_data.get("service_name")
                if service_type or service_name:
                    context.profile_data["service_type"] = service_type or service_name
                    
                    # تهيئة VehicleManager
                    if "manager" not in context.vehicle_data:
                        vm = VehicleManager(context.conversation_id)
                        vm.start_new_vehicle()
                        context.vehicle_data["manager"] = vm.to_dict()
                    
                    context.current_stage = ConversationStage.COLLECTING_VEHICLE
                    self.logger.info(f"🧠 AI Transition: SELECTING_SERVICE -> COLLECTING_VEHICLE")
                    return True
        
        # SHOWING_OFFERS -> OFFER_DETAILS or COLLECTING_PROFILE
        elif stage == ConversationStage.SHOWING_OFFERS:
            # Handle offer selection by number or name
            if intent == UserIntent.SELECT_OFFER or intent == UserIntent.CONFIRM:
                offer_num = ai_result.extracted_data.get("offer_number")
                offer_name = ai_result.extracted_data.get("company_name", "")
                
                # Try to find offer by number first
                selected_idx = None
                if offer_num and context.offers_shown:
                    try:
                        idx = int(offer_num) - 1
                        if 0 <= idx < len(context.offers_shown):
                            selected_idx = idx
                    except (ValueError, IndexError):
                        pass
                
                # Try to find offer by company name
                if selected_idx is None and offer_name and context.offers_shown:
                    name_lower = offer_name.lower()
                    for idx, offer in enumerate(context.offers_shown):
                        company = offer.get("company", "").lower()
                        if name_lower in company or company in name_lower:
                            selected_idx = idx
                            break
                
                # Also check raw message for company names
                if selected_idx is None and context.offers_shown:
                    msg_lower = message.lower()
                    company_keywords = {
                        "راجحي": "الراجحي",
                        "تعاونية": "التعاونية",
                        "ميدغلف": "ميدغلف",
                        "ولاء": "ولاء",
                        "سلامة": "سلامة",
                        "أكسا": "أكسا",
                        "ملاذ": "ملاذ",
                        "تكافل": "الراجحي"
                    }
                    for keyword, target in company_keywords.items():
                        if keyword in msg_lower:
                            for idx, offer in enumerate(context.offers_shown):
                                if target in offer.get("company", ""):
                                    selected_idx = idx
                                    break
                            if selected_idx is not None:
                                break
                
                # If offer was selected, save it and show offer details
                if selected_idx is not None and context.offers_shown:
                    context.selected_offer = context.offers_shown[selected_idx]
                    context.selected_offer_id = selected_idx + 1
                    # الانتقال إلى OFFER_DETAILS لعرض تفاصيل العرض الكاملة
                    context.current_stage = ConversationStage.OFFER_DETAILS
                    self.logger.info(f"🧠 AI Transition: SHOWING_OFFERS -> OFFER_DETAILS (offer #{selected_idx + 1})")
                    return True
        
        # CONFIRMING_VEHICLE -> SHOWING_OFFERS (عند التأكيد وجلب العروض)
        elif stage == ConversationStage.CONFIRMING_VEHICLE:
            if intent == UserIntent.CONFIRM:
                # جلب العروض وحفظها في السياق
                self._fetch_and_save_offers(context)
                context.current_stage = ConversationStage.SHOWING_OFFERS
                self.logger.info("🧠 AI Transition: CONFIRMING_VEHICLE -> SHOWING_OFFERS")
                return True
        
        # OFFER_DETAILS -> COLLECTING_PROFILE
        elif stage == ConversationStage.OFFER_DETAILS:
            if intent == UserIntent.CONFIRM:
                context.current_stage = ConversationStage.COLLECTING_PROFILE
                self.logger.info("🧠 AI Transition: OFFER_DETAILS -> COLLECTING_PROFILE")
                return True
        
        # Also check for auto-transitions
        return self._handle_auto_transition(context, message, extracted_data)
    
    def _reset_context(self, context: ConversationContext):
        """إعادة تعيين السياق (كل شيء)"""
        context.current_stage = ConversationStage.GREETING
        context.profile_data = {}
        context.vehicle_data = {}
        context.offers_shown = []
        context.selected_offer = None
        context.pending_action = None
    
    def _reset_for_new_request(self, context: ConversationContext):
        """إعادة تعيين للطلب الجديد مع الحفاظ على البيانات الشخصية"""
        old_profile = context.profile_data.copy() if context.profile_data else {}
        context.current_stage = ConversationStage.GREETING
        context.profile_data = old_profile  # الاحتفاظ بالهوية والميلاد
        context.vehicle_data = {}
        context.offers_shown = []
        context.selected_offer = None
        context.pending_action = None
        self.logger.info(f"🔄 Session reset for new request, profile kept: {list(old_profile.keys())}")
    
    def _fetch_and_save_offers(self, context: ConversationContext):
        """
        جلب العروض من قاعدة البيانات وحفظها في السياق
        """
        try:
            # جلب قيمة السيارة
            vehicle_value = 0
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
                if vm.current_vehicle and vm.current_vehicle.value:
                    vehicle_value = vm.current_vehicle.value
            
            # محاولة جلب العروض من DB
            try:
                from app.engine.sql_engine import insurance_sql_engine
                result = insurance_sql_engine._execute_sql(
                    "SELECT * FROM offers WHERE is_active = true ORDER BY price ASC LIMIT 5"
                )
                if result and result.get("data") and len(result["data"]) > 0:
                    context.offers_shown = result["data"]
                    self.logger.info(f"✅ Fetched {len(result['data'])} offers from DB")
                    return
            except Exception as e:
                self.logger.warning(f"Could not fetch from DB: {e}")
            
            # العروض الافتراضية بناءً على قيمة السيارة
            base_price = max(vehicle_value * 0.03, 1500)
            
            context.offers_shown = [
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
            self.logger.info(f"✅ Created {len(context.offers_shown)} default offers")
            
        except Exception as e:
            self.logger.error(f"Error fetching offers: {e}")
            context.offers_shown = []


# Global instance
stage_transition_manager = StageTransitionManager()

