"""
SAIA Insurance Broker Platform - Smart Stage Manager
Intelligent conversation handling with LLM integration
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import re

from app.core.constants import ConversationStage, InputType
from app.engine.session_manager import ConversationContext, session_manager
from app.engine.rule_parser import RuleBasedParser
from app.engine.vehicle_manager import VehicleManager

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """Result of processing a stage"""
    success: bool
    response_message: str
    next_stage: Optional[ConversationStage] = None
    data_collected: Dict[str, Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "response_message": self.response_message,
            "next_stage": self.next_stage.value if self.next_stage else None,
            "data_collected": self.data_collected,
            "error": self.error
        }


class SmartStageManager:
    """
    Intelligent Stage Manager with LLM integration.
    
    Key features:
    1. Rule-based parsing for clear inputs (fast)
    2. LLM fallback for unclear inputs (smart)
    3. Context-aware responses
    4. Handles edge cases gracefully
    """
    
    def __init__(self):
        self.session_manager = session_manager
        self.parser = RuleBasedParser()
        self.llm_client = None
        self._init_llm()
    
    def _init_llm(self):
        """Initialize LLM client if available"""
        try:
            from app.llm.gemini_client import gemini_client
            self.llm_client = gemini_client
            if self.llm_client.model:
                logger.info("✅ LLM (Gemini) initialized successfully")
            else:
                logger.warning("⚠️ Gemini API key not configured, using fallback responses")
        except Exception as e:
            logger.warning(f"LLM initialization failed: {e}")
    
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        phone: Optional[str] = None
    ) -> StageResult:
        """Main entry point - process incoming message intelligently"""
        
        logger.info(f"Processing: {message[:50]}...")
        
        # Check session
        session_check = await self.session_manager.check_session(conversation_id)
        context = await self.session_manager.get_context(conversation_id)
        
        # Handle new session
        if session_check.action == "start_new":
            context = await self.session_manager.create_context(conversation_id, phone)
            return await self._smart_greeting(context, message)
        
        # Handle session resume
        if session_check.action == "ask_resume":
            return await self._handle_resume(context, message, conversation_id, phone)
        
        # Active session - smart processing
        return await self._smart_process(context, message)
    
    async def _smart_greeting(self, context: ConversationContext, message: str) -> StageResult:
        """Smart greeting that understands user intent"""
        
        context.current_stage = ConversationStage.GREETING
        
        # Check if user already has a clear intent
        intent = await self._classify_intent(message)
        
        if intent == "new_insurance":
            # Skip greeting, go directly to profile collection
            context.current_stage = ConversationStage.COLLECTING_PROFILE
            await self.session_manager.update_context(context)
            return await self._start_profile_collection(context, message)
        
        # Generate smart greeting response
        response = await self._generate_smart_response(
            message, context, "greeting",
            fallback="""السلام عليكم! 👋
أهلاً بك في منصة التأمين الذكي

كيف أقدر أساعدك؟
1️⃣ إصدار تأمين جديد
2️⃣ عرض وثائقي السابقة
3️⃣ متابعة طلب

اختر الرقم أو اكتب ما تريد 👇"""
        )
        
        context.awaiting_input_type = InputType.CHOICE_NUMBER.value
        await self.session_manager.update_context(context)
        
        return StageResult(
            success=True,
            response_message=response,
            next_stage=ConversationStage.GREETING
        )
    
    async def _smart_process(self, context: ConversationContext, message: str) -> StageResult:
        """Smart processing based on current stage"""
        
        stage = context.current_stage
        
        # Stage handlers map
        handlers = {
            ConversationStage.GREETING: self._handle_greeting_input,
            ConversationStage.COLLECTING_PROFILE: self._handle_profile_smart,
            ConversationStage.COLLECTING_VEHICLE: self._handle_vehicle_smart,
            ConversationStage.ASK_ANOTHER_VEHICLE: self._handle_another_vehicle,
            ConversationStage.SHOWING_OFFERS: self._fetch_and_show_offers,
            ConversationStage.AWAITING_SELECTION: self._handle_offer_selection,
            ConversationStage.CONFIRMATION: self._handle_confirmation,
            ConversationStage.PENDING_PAYMENT: self._handle_payment,
            ConversationStage.DONE: self._handle_done,
        }
        
        handler = handlers.get(stage, self._smart_greeting)
        result = await handler(context, message)
        await self.session_manager.update_context(context)
        
        return result
    
    async def _handle_greeting_input(self, context: ConversationContext, message: str) -> StageResult:
        """Handle greeting input intelligently"""
        
        # Try rule-based first
        parse_result = self.parser.parse(message, InputType.CHOICE_NUMBER, 3)
        
        if parse_result.matched and isinstance(parse_result.value, int):
            choice = parse_result.value
            
            if choice == 1:
                context.current_stage = ConversationStage.COLLECTING_PROFILE
                return await self._start_profile_collection(context, message)
            elif choice == 2:
                return await self._handle_documents(context)
            elif choice == 3:
                return await self._handle_tracking(context)
        
        # Check intent using LLM
        intent = await self._classify_intent(message)
        
        if intent == "new_insurance":
            context.current_stage = ConversationStage.COLLECTING_PROFILE
            return await self._start_profile_collection(context, message)
        
        if intent in ("question", "complaint"):
            # Answer and redirect
            response = await self._generate_smart_response(
                message, context, "greeting",
                fallback="شكراً لتواصلك! كيف أقدر أساعدك؟\n\n1️⃣ إصدار تأمين\n2️⃣ عرض وثائقي\n3️⃣ متابعة طلب"
            )
            return StageResult(success=True, response_message=response, next_stage=ConversationStage.GREETING)
        
        # Unknown - be helpful
        response = await self._generate_smart_response(
            message, context, "greeting",
            fallback="أهلاً بك! 👋\n\nكيف أقدر أساعدك؟\n1️⃣ تأمين جديد\n2️⃣ وثائقي\n3️⃣ متابعة طلب"
        )
        return StageResult(success=True, response_message=response, next_stage=ConversationStage.GREETING)
    
    async def _start_profile_collection(self, context: ConversationContext, message: str = "") -> StageResult:
        """Start profile collection with smart response"""
        
        context.last_question = "national_id"
        context.awaiting_input_type = InputType.NATIONAL_ID.value
        
        response = await self._generate_smart_response(
            message, context, "collecting_profile",
            fallback="""أهلاً! 📝

لإصدار التأمين، أحتاج رقم الهوية الوطنية أو الإقامة
(10 أرقام، يبدأ بـ 1 أو 2)

اكتب الرقم 👇"""
        )
        
        return StageResult(
            success=True,
            response_message=response,
            next_stage=ConversationStage.COLLECTING_PROFILE
        )
    
    async def _handle_profile_smart(self, context: ConversationContext, message: str) -> StageResult:
        """Handle profile collection with smart fallback"""
        
        current_field = context.last_question or "national_id"
        
        # ===============================
        # NATIONAL ID
        # ===============================
        if current_field == "national_id":
            # Try extracting national ID from message
            national_id = self._extract_national_id(message)
            
            if national_id:
                context.profile_data["national_id"] = national_id
                context.last_question = "birth_date"
                context.awaiting_input_type = InputType.BIRTH_DATE.value
                
                return StageResult(
                    success=True,
                    response_message=f"""✅ تم حفظ رقم الهوية

الآن، تاريخ ميلادك؟
(مثال: 1990/05/15 أو 25/3/1990)""",
                    next_stage=ConversationStage.COLLECTING_PROFILE,
                    data_collected={"national_id": national_id}
                )
            
            # Handle special cases
            if any(word in message for word in ["لا يوجد", "ما عندي", "مافي", "ماعندي", "لا اعرف", "ما اعرف"]):
                response = await self._generate_smart_response(
                    message, context, "collecting_profile",
                    fallback="""لا تقلق! 😊

رقم الهوية ضروري للتأمين لأن الشركات تحتاجه للتحقق.

لو ما تعرف رقمك:
- تلقاه في بطاقة الأحوال
- أو في أبشر

لو عندك استفسار آخر، أنا هنا للمساعدة 👇"""
                )
                return StageResult(success=True, response_message=response, next_stage=ConversationStage.COLLECTING_PROFILE)
            
            # Unrecognized input - be helpful
            response = await self._generate_smart_response(
                message, context, "collecting_profile",
                fallback="""ما قدرت أتعرف على رقم الهوية 🤔

الرقم لازم يكون:
✓ 10 أرقام
✓ يبدأ بـ 1 (سعودي) أو 2 (مقيم)

مثال: 1122334455

حاول مرة ثانية 👇"""
            )
            return StageResult(success=True, response_message=response, next_stage=ConversationStage.COLLECTING_PROFILE)
        
        # ===============================
        # BIRTH DATE
        # ===============================
        elif current_field == "birth_date":
            # Accept various date formats
            context.profile_data["birth_date"] = message
            context.last_question = "phone"
            context.awaiting_input_type = InputType.PHONE.value
            
            return StageResult(
                success=True,
                response_message="""✅ تم!

رقم جوالك؟ (للتواصل معك)
أو اكتب "تخطي" إذا تبي نكمل بدونه""",
                next_stage=ConversationStage.COLLECTING_PROFILE,
                data_collected={"birth_date": message}
            )
        
        # ===============================
        # PHONE
        # ===============================
        elif current_field == "phone":
            if self.parser.is_negative(message) or any(w in message for w in ["تخطي", "skip", "لا", "بدون"]):
                pass
            else:
                phone = self._extract_phone(message)
                if phone:
                    context.profile_data["phone"] = phone
            
            # Show summary
            from app.core.security import DataMasker
            masked_id = DataMasker.mask_national_id(context.profile_data.get("national_id", ""))
            
            context.last_question = "confirm_profile"
            context.awaiting_input_type = InputType.AFFIRMATIVE.value
            
            return StageResult(
                success=True,
                response_message=f"""✅ بياناتك:

📋 الهوية: {masked_id}
📅 الميلاد: {context.profile_data.get('birth_date', '')}
📱 الجوال: {context.profile_data.get('phone', 'لم يُحدد')}

هل البيانات صحيحة؟ (نعم / تعديل)""",
                next_stage=ConversationStage.COLLECTING_PROFILE
            )
        
        # ===============================
        # CONFIRM PROFILE
        # ===============================
        elif current_field == "confirm_profile":
            if self.parser.is_affirmative(message):
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
                return await self._start_vehicle_collection(context)
            elif self.parser.is_negative(message) or "تعديل" in message:
                context.profile_data = {}
                return await self._start_profile_collection(context, message)
            else:
                # Ask LLM
                intent = await self._classify_intent(message)
                if intent == "confirm":
                    context.current_stage = ConversationStage.COLLECTING_VEHICLE
                    return await self._start_vehicle_collection(context)
                
                response = await self._generate_smart_response(
                    message, context, "collecting_profile",
                    fallback="هل البيانات صحيحة؟\n\n✅ نعم - لإكمال\n✏️ تعديل - لتغيير البيانات"
                )
                return StageResult(success=True, response_message=response, next_stage=ConversationStage.COLLECTING_PROFILE)
        
        return await self._start_profile_collection(context, message)
    
    async def _start_vehicle_collection(self, context: ConversationContext) -> StageResult:
        """Start vehicle data collection"""
        
        vehicle_manager = VehicleManager(context.conversation_id)
        vehicle_manager.start_new_vehicle()
        context.vehicle_data["manager"] = vehicle_manager.to_dict()
        
        context.last_question = "registration_type"
        context.awaiting_input_type = InputType.CHOICE_NUMBER.value
        
        return StageResult(
            success=True,
            response_message="""الآن بيانات السيارة 🚗

ما نوع التسجيل؟
1️⃣ لوحة سعودية
2️⃣ رقم تسلسلي (سيارة جديدة)
3️⃣ بطاقة جمركية""",
            next_stage=ConversationStage.COLLECTING_VEHICLE
        )
    
    async def _handle_vehicle_smart(self, context: ConversationContext, message: str) -> StageResult:
        """Handle vehicle collection with smart fallback"""
        
        manager_data = context.vehicle_data.get("manager", {})
        vehicle_manager = VehicleManager.from_dict(manager_data) if manager_data else VehicleManager(context.conversation_id)
        
        if not vehicle_manager.vehicles:
            vehicle_manager.start_new_vehicle()
        
        current_field = context.last_question or "registration_type"
        
        # ===============================
        # REGISTRATION TYPE
        # ===============================
        if current_field == "registration_type":
            parse_result = self.parser.parse(message, InputType.CHOICE_NUMBER, 3)
            if parse_result.matched:
                reg_types = {1: "plate", 2: "serial", 3: "custom"}
                vehicle_manager.update_current(registration_type=reg_types.get(parse_result.value, "plate"))
                context.last_question = "plate_number"
                context.vehicle_data["manager"] = vehicle_manager.to_dict()
                
                prompts = {
                    1: "أعطني رقم اللوحة\n(مثال: أ ب ت 1234 أو ABT 1234)",
                    2: "أعطني الرقم التسلسلي للسيارة",
                    3: "أعطني رقم البطاقة الجمركية"
                }
                return StageResult(success=True, response_message=prompts.get(parse_result.value, prompts[1]), next_stage=ConversationStage.COLLECTING_VEHICLE)
            
            # Smart fallback
            response = await self._generate_smart_response(
                message, context, "collecting_vehicle",
                fallback="اختر نوع التسجيل:\n\n1️⃣ لوحة سعودية\n2️⃣ رقم تسلسلي\n3️⃣ بطاقة جمركية"
            )
            return StageResult(success=True, response_message=response, next_stage=ConversationStage.COLLECTING_VEHICLE)
        
        # ===============================
        # PLATE NUMBER
        # ===============================
        elif current_field == "plate_number":
            vehicle_manager.update_current(plate_no=message)
            context.last_question = "vehicle_info"
            context.vehicle_data["manager"] = vehicle_manager.to_dict()
            
            return StageResult(
                success=True,
                response_message=f"""✅ تم: {message}

ما نوع السيارة؟
(مثال: تويوتا كامري 2022)
أو (هيونداي سوناتا 2021)""",
                next_stage=ConversationStage.COLLECTING_VEHICLE
            )
        
        # ===============================
        # VEHICLE INFO
        # ===============================
        elif current_field == "vehicle_info":
            # Extract vehicle info
            vehicle_info = await self._extract_vehicle_info(message)
            vehicle_manager.update_current(**vehicle_info)
            
            context.last_question = "vehicle_value"
            context.vehicle_data["manager"] = vehicle_manager.to_dict()
            
            v = vehicle_manager.current_vehicle
            return StageResult(
                success=True,
                response_message=f"""✅ تم:
• الشركة: {v.brand or 'غير محدد'}
• الموديل: {v.model or 'غير محدد'}
• السنة: {v.year or '2024'}

كم القيمة التقديرية للسيارة؟ (بالريال)
مثال: 80000 أو 120 ألف""",
                next_stage=ConversationStage.COLLECTING_VEHICLE
            )
        
        # ===============================
        # VEHICLE VALUE
        # ===============================
        elif current_field == "vehicle_value":
            value = self._extract_price(message)
            vehicle_manager.update_current(value=value)
            vehicle_manager.current_vehicle.check_completeness()
            context.vehicle_data["manager"] = vehicle_manager.to_dict()
            
            summary = vehicle_manager.get_summary()
            
            context.current_stage = ConversationStage.ASK_ANOTHER_VEHICLE
            context.last_question = "another_vehicle"
            
            return StageResult(
                success=True,
                response_message=f"""✅ تم حفظ السيارة:

{summary}

هل تريد تأمين سيارة أخرى؟
1️⃣ نعم
2️⃣ لا، نكمل""",
                next_stage=ConversationStage.ASK_ANOTHER_VEHICLE
            )
        
        return await self._start_vehicle_collection(context)
    
    async def _handle_another_vehicle(self, context: ConversationContext, message: str) -> StageResult:
        """Handle 'add another vehicle' choice"""
        
        parse_result = self.parser.parse(message, InputType.CHOICE_NUMBER, 2)
        
        if parse_result.matched:
            if parse_result.value == 1:
                manager_data = context.vehicle_data.get("manager", {})
                vehicle_manager = VehicleManager.from_dict(manager_data)
                vehicle_manager.start_new_vehicle()
                context.vehicle_data["manager"] = vehicle_manager.to_dict()
                context.current_stage = ConversationStage.COLLECTING_VEHICLE
                context.last_question = "registration_type"
                
                return StageResult(
                    success=True,
                    response_message=f"""تمام! السيارة #{vehicle_manager.vehicle_count} 🚗

نوع التسجيل؟
1️⃣ لوحة سعودية
2️⃣ رقم تسلسلي
3️⃣ بطاقة جمركية""",
                    next_stage=ConversationStage.COLLECTING_VEHICLE
                )
            elif parse_result.value == 2:
                context.current_stage = ConversationStage.FETCHING_OFFERS
                return await self._fetch_and_show_offers(context, message)
        
        # Check if affirmative/negative
        if self.parser.is_affirmative(message):
            return await self._handle_another_vehicle(context, "1")
        if self.parser.is_negative(message):
            return await self._handle_another_vehicle(context, "2")
        
        return StageResult(
            success=True,
            response_message="هل تريد إضافة سيارة أخرى؟\n\n1️⃣ نعم\n2️⃣ لا",
            next_stage=ConversationStage.ASK_ANOTHER_VEHICLE
        )
    
    async def _fetch_and_show_offers(self, context: ConversationContext, message: str = "") -> StageResult:
        """Fetch and display offers"""
        
        offers = [
            {"id": 1, "type": "comprehensive", "price": 2850, "features": ["تغطية شاملة + سرقة + حريق", "سيارة بديلة 7 أيام"]},
            {"id": 2, "type": "comprehensive", "price": 3200, "features": ["تغطية شاملة + كوارث", "مساعدة 24/7"]},
            {"id": 3, "type": "tpl", "price": 1100, "features": ["ضد الغير فقط", "السعر الأقل"]},
            {"id": 4, "type": "tpl_plus", "price": 1450, "features": ["ضد الغير + حريق وسرقة", "خصم تجديد 10%"]},
        ]
        
        context.offers_shown = offers
        context.current_stage = ConversationStage.AWAITING_SELECTION
        context.last_question = "offer_selection"
        context.awaiting_input_type = InputType.CHOICE_NUMBER.value
        
        type_names = {"comprehensive": "شامل", "tpl": "ضد الغير", "tpl_plus": "ضد الغير+"}
        
        lines = ["🎯 وجدنا لك 4 عروض:\n"]
        for i, offer in enumerate(offers):
            lines.append(f"{i+1}️⃣ {type_names.get(offer['type'], '')} - {offer['price']:,} ريال")
            for f in offer['features']:
                lines.append(f"   ✓ {f}")
            lines.append("")
        
        lines.append("اختر رقم العرض 👇")
        
        return StageResult(
            success=True,
            response_message="\n".join(lines),
            next_stage=ConversationStage.AWAITING_SELECTION
        )
    
    async def _handle_offer_selection(self, context: ConversationContext, message: str) -> StageResult:
        """Handle offer selection"""
        
        offers = context.offers_shown or []
        max_choice = len(offers)
        
        parse_result = self.parser.parse(message, InputType.CHOICE_NUMBER, max_choice)
        
        if parse_result.matched and 1 <= parse_result.value <= max_choice:
            selected = offers[parse_result.value - 1]
            context.selected_offer_id = selected["id"]
            context.selected_offer = selected
            context.current_stage = ConversationStage.CONFIRMATION
            
            return await self._show_confirmation(context)
        
        # Smart response for questions about offers
        response = await self._generate_smart_response(
            message, context, "showing_offers",
            fallback=f"اختر رقم العرض من 1 إلى {max_choice} 👇"
        )
        return StageResult(success=True, response_message=response, next_stage=ConversationStage.AWAITING_SELECTION)
    
    async def _show_confirmation(self, context: ConversationContext) -> StageResult:
        """Show order confirmation"""
        
        from app.core.security import DataMasker
        
        profile = context.profile_data
        offer = context.selected_offer
        
        manager_data = context.vehicle_data.get("manager", {})
        vehicle_manager = VehicleManager.from_dict(manager_data)
        
        masked_id = DataMasker.mask_national_id(profile.get("national_id", ""))
        
        type_names = {"comprehensive": "تأمين شامل", "tpl": "ضد الغير", "tpl_plus": "ضد الغير+"}
        offer_type = type_names.get(offer.get("type", ""), "تأمين")
        
        price = offer.get("price", 0)
        vat = price * 0.15
        total = price + vat
        
        context.last_question = "confirmation"
        context.awaiting_input_type = InputType.CHOICE_NUMBER.value
        
        return StageResult(
            success=True,
            response_message=f"""📋 ملخص الطلب:

👤 العميل: {masked_id}
🚗 السيارات: {vehicle_manager.vehicle_count}
🛡️ التأمين: {offer_type}

💰 السعر: {price:,} ريال
   + ضريبة: {vat:,.0f} ريال
   ━━━━━━━━━━
   الإجمالي: {total:,.0f} ريال

1️⃣ تأكيد وإنشاء الفاتورة
2️⃣ تعديل
3️⃣ إلغاء""",
            next_stage=ConversationStage.CONFIRMATION
        )
    
    async def _handle_confirmation(self, context: ConversationContext, message: str) -> StageResult:
        """Handle confirmation"""
        
        parse_result = self.parser.parse(message, InputType.CHOICE_NUMBER, 3)
        
        if parse_result.matched:
            if parse_result.value == 1:
                return await self._create_invoice(context)
            elif parse_result.value == 2:
                context.current_stage = ConversationStage.COLLECTING_PROFILE
                return await self._start_profile_collection(context, message)
            elif parse_result.value == 3:
                context.current_stage = ConversationStage.GREETING
                return await self._smart_greeting(context, message)
        
        if self.parser.is_affirmative(message):
            return await self._create_invoice(context)
        
        response = await self._generate_smart_response(
            message, context, "confirmation",
            fallback="اختر:\n1️⃣ تأكيد\n2️⃣ تعديل\n3️⃣ إلغاء"
        )
        return StageResult(success=True, response_message=response, next_stage=ConversationStage.CONFIRMATION)
    
    async def _create_invoice(self, context: ConversationContext) -> StageResult:
        """Create invoice with idempotency"""
        from app.core.idempotency import idempotency_manager
        from datetime import timedelta
        import random
        
        if not context.order_id:
            context.order_id = random.randint(10000, 99999)
        
        idem_result = await idempotency_manager.check_and_lock(
            str(context.order_id), "invoice", "create"
        )
        
        if idem_result.is_duplicate and idem_result.original_result:
            invoice = idem_result.original_result
            context.invoice_id = invoice.get("id")
            context.current_stage = ConversationStage.PENDING_PAYMENT
            
            return StageResult(
                success=True,
                response_message=f"""✅ الفاتورة موجودة!

🧾 {invoice.get('number')}
💰 {invoice.get('total'):,.0f} ريال

اكتب "تم الدفع" بعد إتمام الدفع 👇""",
                next_stage=ConversationStage.PENDING_PAYMENT
            )
        
        offer = context.selected_offer or {}
        price = offer.get("price", 0)
        vat = price * 0.15
        total = price + vat
        
        invoice_number = f"INV-2026-{random.randint(10000, 99999)}"
        
        invoice = {
            "id": random.randint(1, 9999),
            "number": invoice_number,
            "amount": price,
            "vat": vat,
            "total": total
        }
        
        await idempotency_manager.mark_completed(
            str(context.order_id), "invoice", "create", invoice
        )
        
        context.invoice_id = invoice["id"]
        context.current_stage = ConversationStage.PENDING_PAYMENT
        context.last_question = "payment"
        context.awaiting_input_type = InputType.PAYMENT_CONFIRM.value
        
        return StageResult(
            success=True,
            response_message=f"""✅ تم إنشاء الفاتورة!

🧾 رقم الفاتورة: {invoice_number}
💰 الإجمالي: {total:,.0f} ريال

⏰ صلاحية: 24 ساعة

━━━━━━━━━━━━━━━━
💳 اكتب "تم الدفع" بعد إتمام الدفع""",
            next_stage=ConversationStage.PENDING_PAYMENT
        )
    
    async def _handle_payment(self, context: ConversationContext, message: str) -> StageResult:
        """Handle payment confirmation"""
        
        parse_result = self.parser.parse(message, InputType.PAYMENT_CONFIRM)
        
        if parse_result.matched or any(w in message for w in ["تم", "دفعت", "paid", "done"]):
            return await self._issue_policy(context)
        
        response = await self._generate_smart_response(
            message, context, "pending_payment",
            fallback="⏳ في انتظار الدفع\n\nاكتب \"تم الدفع\" بعد إتمام الدفع 👇"
        )
        return StageResult(success=True, response_message=response, next_stage=ConversationStage.PENDING_PAYMENT)
    
    async def _issue_policy(self, context: ConversationContext) -> StageResult:
        """Issue policy"""
        import random
        from datetime import date, timedelta
        
        policy_number = f"POL-2026-{random.randint(10000, 99999)}"
        start_date = date.today()
        end_date = start_date + timedelta(days=365)
        
        context.policy_id = random.randint(1, 9999)
        context.current_stage = ConversationStage.DONE
        
        manager_data = context.vehicle_data.get("manager", {})
        vehicle_manager = VehicleManager.from_dict(manager_data)
        v = vehicle_manager.current_vehicle
        
        return StageResult(
            success=True,
            response_message=f"""🎉 تم إصدار الوثيقة!

📄 رقم الوثيقة: {policy_number}
🛡️ التغطية: {start_date} - {end_date}
🚗 السيارة: {v.brand if v else ''} {v.model if v else ''}

📎 [تحميل الوثيقة PDF]

شكراً لثقتك بنا! 🙏""",
            next_stage=ConversationStage.DONE
        )
    
    async def _handle_done(self, context: ConversationContext, message: str) -> StageResult:
        """Handle conversation after completion"""
        
        response = await self._generate_smart_response(
            message, context, "greeting",
            fallback="""شكراً لتواصلك! 🙏

هل تحتاج مساعدة أخرى؟
1️⃣ تأمين سيارة أخرى
2️⃣ عرض وثائقي
3️⃣ لا، شكراً"""
        )
        
        context.current_stage = ConversationStage.GREETING
        return StageResult(success=True, response_message=response, next_stage=ConversationStage.GREETING)
    
    async def _handle_resume(self, context, message, conversation_id, phone) -> StageResult:
        """Handle session resume"""
        parse_result = self.parser.parse(message, InputType.CHOICE_NUMBER, 2)
        
        if parse_result.matched:
            if parse_result.value == 1:
                context = await self.session_manager.resume_session(conversation_id)
                return await self._smart_process(context, "استمر")
            elif parse_result.value == 2:
                await self.session_manager.clear_session(conversation_id)
                context = await self.session_manager.create_context(conversation_id, phone)
                return await self._smart_greeting(context, message)
        
        resume_msg = self.session_manager.generate_resume_message(
            await self.session_manager.check_session(conversation_id), context
        )
        return StageResult(success=True, response_message=resume_msg, next_stage=ConversationStage.SESSION_RESUME)
    
    async def _handle_documents(self, context) -> StageResult:
        return StageResult(success=True, response_message="📂 لا توجد وثائق حالياً.\n\nللعودة اكتب 'رجوع'", next_stage=ConversationStage.DOCUMENTS_VIEW)
    
    async def _handle_tracking(self, context) -> StageResult:
        return StageResult(success=True, response_message="📋 لا توجد طلبات نشطة.\n\nللعودة اكتب 'رجوع'", next_stage=ConversationStage.ORDER_TRACKING)
    
    # =========================================
    # Helper Methods
    # =========================================
    
    async def _classify_intent(self, message: str) -> str:
        """Classify user intent"""
        if self.llm_client and self.llm_client.model:
            return await self.llm_client.classify_intent(message)
        
        # Fallback classification
        lower = message.lower()
        if any(w in lower for w in ["تأمين", "سيارة", "insurance", "جديد"]):
            return "new_insurance"
        if any(w in lower for w in ["نعم", "تمام", "موافق", "yes", "ok"]):
            return "confirm"
        if any(w in lower for w in ["لا", "الغي", "no", "cancel"]):
            return "reject"
        return "unclear"
    
    async def _generate_smart_response(self, message: str, context: ConversationContext, stage: str, fallback: str) -> str:
        """Generate smart response using LLM or fallback"""
        if self.llm_client and self.llm_client.model:
            try:
                response = await self.llm_client.generate_response(
                    message, context.to_dict(), stage
                )
                if response:
                    return response
            except Exception as e:
                logger.warning(f"LLM error: {e}")
        
        return fallback
    
    def _extract_national_id(self, message: str) -> Optional[str]:
        """Extract national ID from message"""
        numbers = re.findall(r'\d+', message)
        for num in numbers:
            if len(num) == 10 and num[0] in ('1', '2'):
                return num
        return None
    
    def _extract_phone(self, message: str) -> Optional[str]:
        """Extract phone number from message"""
        digits = re.sub(r'\D', '', message)
        if len(digits) >= 9:
            if digits.startswith('966'):
                return '0' + digits[3:]
            if digits.startswith('5') and len(digits) == 9:
                return '0' + digits
            if digits.startswith('05') and len(digits) == 10:
                return digits
        return None
    
    async def _extract_vehicle_info(self, message: str) -> Dict[str, Any]:
        """Extract vehicle info from message"""
        parts = message.split()
        info = {"brand": "", "model": "", "year": 2024}
        
        if len(parts) >= 1:
            info["brand"] = parts[0]
        if len(parts) >= 2:
            info["model"] = parts[1]
        if len(parts) >= 3 and parts[-1].isdigit():
            year = int(parts[-1])
            if 1990 <= year <= 2030:
                info["year"] = year
            elif 1400 <= year <= 1450:
                info["year"] = year + 579  # Hijri to Gregorian approx
        
        return info
    
    def _extract_price(self, message: str) -> int:
        """Extract price value from message"""
        # Handle "80 ألف" or "80000" or "80,000"
        clean = message.replace(',', '').replace('،', '')
        
        if 'ألف' in clean or 'الف' in clean:
            numbers = re.findall(r'\d+', clean)
            if numbers:
                return int(numbers[0]) * 1000
        
        numbers = re.findall(r'\d+', clean)
        if numbers:
            return int(numbers[0])
        
        return 50000  # Default


# Global instance - replace the old one
smart_stage_manager = SmartStageManager()
