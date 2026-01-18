"""
SAIA Insurance Broker - Professional AI Conversation Engine (Simplified)
المحرك الاحترافي للمحادثات - النسخة المبسطة

تم تقسيم الوظائف إلى وحدات منفصلة:
- conversation/ - إدارة السجل والبرومبتات
- extractors/ - استخراج البيانات
- transitions/ - إدارة الانتقالات
- db_operations - عمليات قاعدة البيانات
"""
import google.generativeai as genai
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import logging
import json

from app.config import settings
from app.core.constants import ConversationStage
from app.engine.session_manager import ConversationContext, session_manager
from app.engine.master_orchestrator import master_orchestrator

# Modular imports
from app.engine.conversation import (
    get_or_create_history,
    clear_history,
    SYSTEM_PROMPT,
    get_stage_info,
    get_data_summary,
)
from app.engine.extractors import data_extractor
from app.engine.transitions import stage_transition_manager
from app.engine.db_operations import db_operations

logger = logging.getLogger(__name__)


@dataclass
class StageResult:
    """نتيجة معالجة المرحلة"""
    success: bool
    response_message: str
    next_stage: Optional[ConversationStage] = None
    data_collected: Dict[str, Any] = None
    error: Optional[str] = None


class ProfessionalInsuranceEngine:
    """
    المحرك الاحترافي للتأمين
    
    مسؤوليات هذا الملف:
    - تنسيق العمل بين الوحدات
    - معالجة الرسائل
    - التواصل مع Gemini
    """
    
    def __init__(self):
        self.model = None
        self.orchestrator = master_orchestrator
        self.ai_analyzer = None
        
        self._init_gemini()
        self._init_ai_analyzer()
        db_operations.initialize()
    
    def _init_gemini(self):
        """تهيئة Gemini"""
        try:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    settings.GEMINI_MODEL,
                    generation_config=genai.GenerationConfig(
                        temperature=0.7,
                        max_output_tokens=800,
                    )
                )
                logger.info(f"✅ Professional Engine initialized with {settings.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Gemini init error: {e}")
    
    def _init_ai_analyzer(self):
        """تهيئة محلل النوايا"""
        try:
            from app.engine.ai_intent_analyzer import ai_intent_analyzer
            self.ai_analyzer = ai_intent_analyzer
            logger.info("✅ AI Intent Analyzer initialized")
        except Exception as e:
            logger.warning(f"Could not init AI analyzer: {e}")
    
    async def process_message(
        self,
        conversation_id: str,
        message: str,
        phone: Optional[str] = None
    ) -> StageResult:
        """معالجة رسالة المستخدم"""
        
        logger.info(f"Processing: {message[:50]}...")
        
        # 1. الحصول على السياق
        session_check = await session_manager.check_session(conversation_id)
        context = await session_manager.get_context(conversation_id)
        
        if session_check.action == "start_new":
            context = await session_manager.create_context(conversation_id, phone)
            clear_history(conversation_id)
        
        # 2. معالجة استئناف الجلسة
        if session_check.action == "ask_resume":
            return await self._handle_resume(context, message, conversation_id, phone, session_check)
        
        # 3. الحصول على سجل المحادثة
        history = get_or_create_history(conversation_id)
        history.add_message("user", message, context.current_stage.value)
        
        # 4. استخراج البيانات
        extracted_data = data_extractor.extract_all(message)
        logger.info(f"🔍 Extracted Data: {extracted_data}")
        
        # 5. تحديث السياق بالبيانات
        stage_transition_manager.update_context_with_data(context, extracted_data)
        
        # 6. تحليل النية بالـ AI
        ai_intent_result = None
        if self.ai_analyzer:
            available_services = db_operations.get_services()
            ai_intent_result = self.ai_analyzer.analyze(
                message=message,
                current_stage=context.current_stage,
                context_data={
                    "profile_data": context.profile_data,
                    "vehicle_data": context.vehicle_data,
                    "selected_service": context.profile_data.get("service_type")
                },
                available_services=available_services
            )
            logger.info(f"🧠 AI Intent: {ai_intent_result.intent.value}")
            
            if ai_intent_result.extracted_data:
                extracted_data.update(ai_intent_result.extracted_data)
                stage_transition_manager.update_context_with_data(context, ai_intent_result.extracted_data)
        
        # 7. تحديد الانتقال
        prev_stage = context.current_stage
        stage_transition_manager.determine_transition(
            context, message, extracted_data, ai_intent_result
        )
        if context.current_stage != prev_stage:
            logger.info(f"🔄 Stage transition: {prev_stage} -> {context.current_stage}")
        
        # 8. بناء البرومبت
        prompt = self._build_prompt(context, message, history, extracted_data)
        
        # 9. الحصول على الرد من Gemini
        try:
            chat = self.model.start_chat(history=[])
            # استخدام prompt فقط بدون SYSTEM_PROMPT لأن master_prompt يحتوي على كل التعليمات
            response = chat.send_message(prompt)
            ai_response = response.text
            
            history.add_message("assistant", ai_response, context.current_stage.value, extracted_data)
            
            # حفظ الرسائل في context لاستعادتها لاحقاً
            context.messages.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat()
            })
            context.messages.append({
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat()
            })
            
            await session_manager.update_context(context)
            
            return StageResult(
                success=True,
                response_message=ai_response,
                next_stage=context.current_stage,
                data_collected=extracted_data
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            return StageResult(
                success=False,
                response_message="عذراً، حدث خطأ. هل يمكنك إعادة المحاولة؟",
                next_stage=context.current_stage,
                error=str(e)
            )
    
    def _build_prompt(
        self,
        context: ConversationContext,
        message: str,
        history,
        extracted_data: Dict
    ) -> str:
        """بناء البرومبت مع أقسام واضحة للبيانات"""
        
        # استخدام Master Prompt من المنسق
        try:
            master_prompt = self.orchestrator.build_master_prompt(context)
        except Exception as e:
            logger.warning(f"Could not build master prompt: {e}")
            master_prompt = ""
        
        # معلومات العروض - استخدام العروض الموجودة في context (لا نستدعي db_operations لتجنب الكتابة فوقها)
        offers_info = ""
        if context.current_stage in (ConversationStage.SHOWING_OFFERS, ConversationStage.AWAITING_SELECTION):
            # استخدام العروض الموجودة في context.offers_shown مباشرة بدلاً من جلبها من db_operations
            if context.offers_shown:
                offers_info = self._format_offers_for_prompt(context.offers_shown)
            else:
                logger.warning("⚠️ No offers in context.offers_shown for SHOWING_OFFERS stage")
        
        # ⭐ قسم البيانات المجمعة والناقصة - واضح جداً للـ AI
        data_status = self._format_data_status(context)
        
        if master_prompt:
            # إضافة معلومات السجل إذا طلبها المستخدم
            history_section = ""
            if hasattr(context, 'history_response') and context.history_response:
                history_info = context.history_response
                if history_info.get('has_history'):
                    current = history_info.get('current_session', {})
                    history_section = f"""
=== 📋 سجل المستخدم (المستخدم يسأل عن سجله) ===
{self._format_user_history(history_info)}

⚠️ المستخدم يسأل عن سجله/تأميناته - أعطه المعلومات أعلاه بأسلوب احترافي!
"""
                else:
                    history_section = """
=== 📋 سجل المستخدم ===
❌ لم نجد سجل سابق لهذا المستخدم.
⚠️ أخبره بذلك واسأله إذا يريد إصدار تأمين جديد.
"""
                # مسح السجل بعد الاستخدام
                context.history_response = None
            
            # إضافة قسم تأكيد الإلغاء إذا كان معلقاً
            cancel_section = ""
            if getattr(context, 'cancel_confirmation_pending', False):
                cancel_section = """
=== ⚠️ طلب إلغاء معلق ===
المستخدم طلب الإلغاء - يجب أن تسأله للتأكيد!
اسأله: "هل أنت متأكد إنك تبي تلغي الطلب؟ كل البيانات اللي أدخلتها راح تنحفظ ويمكنك استكمالها لاحقاً 😊"
إذا قال نعم/أكيد = أخبره تم الإلغاء والسلام عليكم
إذا قال لا = أخبره ممتاز نكمل ووين كنا
"""

            return f"""{master_prompt}

=== ⚠️ البيانات المجمعة (لا تطلبها مرة أخرى!) ===
{data_status}
{history_section}
{cancel_section}
=== سجل المحادثة ===
{history.get_history_text(8)}

=== البيانات المستخرجة الآن ===
{json.dumps(extracted_data, ensure_ascii=False) if extracted_data else 'لا توجد بيانات جديدة'}

{offers_info}

=== رسالة العميل ===
{message}

⛔⛔⛔ قواعد صارمة جداً ⛔⛔⛔
1. لا تطلب بيانات موجودة في قسم "البيانات المجمعة"!
2. ⛔ ممنوع تماماً إنشاء بيانات افتراضية أو وهمية!
3. ⛔ إذا طلب المستخدم "افرض" أو "اختر من راسك" أو "افترض" = ارفض بلطف واطلب البيانات الحقيقية
4. ⛔ البيانات يجب أن تأتي من العميل فقط وليس من خيالك!
5. رد مثال للرفض: "عذراً، أحتاج البيانات الحقيقية منك 😊 ما أقدر أفترض بيانات. أعطني [البيانات المطلوبة]"

ردك:"""

        
        # Fallback
        stage_info = get_stage_info(context)
        
        return f"""=== حالة المحادثة ===
📍 المرحلة: {stage_info['name']}
📋 الوصف: {stage_info['description']}

=== ⚠️ البيانات المجمعة ===
{data_status}

=== السجل ===
{history.get_history_text(8)}

{offers_info}

=== الرسالة ===
{message}

⛔ لا تطلب بيانات موجودة!
ردك:"""
    
    def _format_data_status(self, context: ConversationContext) -> str:
        """تنسيق حالة البيانات بشكل واضح"""
        lines = []
        
        # بيانات السيارة
        lines.append("🚗 بيانات السيارة:")
        manager_data = context.vehicle_data.get("manager", {})
        if manager_data:
            from app.engine.vehicle_manager import VehicleManager
            vm = VehicleManager.from_dict(manager_data)
            if vm.current_vehicle:
                v = vm.current_vehicle
                lines.append(f"   {'✅' if v.brand else '❌'} النوع: {v.brand or 'مطلوب'}")
                lines.append(f"   {'✅' if v.model else '⚪'} الموديل: {v.model or 'اختياري'}")
                lines.append(f"   {'✅' if v.year else '❌'} السنة: {v.year or 'مطلوب'}")
                lines.append(f"   {'✅' if v.value else '❌'} القيمة: {v.value or 'مطلوب'}")
                lines.append(f"   {'✅' if v.plate_no else '❌'} اللوحة: {v.plate_no or 'مطلوب'}")
                lines.append(f"   📊 مكتملة؟ {'✅ نعم' if v.is_complete else '❌ لا'}")
            else:
                lines.append("   ❌ لم تُجمع أي بيانات بعد")
        else:
            lines.append("   ❌ لم تُجمع أي بيانات بعد")
        
        # بيانات الملف الشخصي
        lines.append("\n👤 البيانات الشخصية:")
        if context.profile_data:
            lines.append(f"   {'✅' if 'national_id' in context.profile_data else '❌'} الهوية: {context.profile_data.get('national_id', 'مطلوب')}")
            lines.append(f"   {'✅' if 'birth_date' in context.profile_data else '❌'} الميلاد: {context.profile_data.get('birth_date', 'مطلوب')}")
            lines.append(f"   {'✅' if 'service_type' in context.profile_data else '❌'} الخدمة: {context.profile_data.get('service_type', 'غير محدد')}")
        else:
            lines.append("   ❌ لم تُجمع أي بيانات بعد")
        
        # العرض المختار
        if context.selected_offer:
            lines.append(f"\n🛡️ العرض المختار: {context.selected_offer.get('company', 'غير محدد')}")
        
        return "\n".join(lines)
    
    def _format_offers_for_prompt(self, offers: list) -> str:
        """تنسيق العروض الموجودة في context للـ AI - بدون تغيير الأسعار"""
        if not offers:
            return ""
        
        lines = ["=== العروض المتوفرة ==="]
        
        for i, offer in enumerate(offers, 1):
            company = offer.get('company', 'شركة')
            # استخدام total_premium أولاً، ثم price كـ fallback
            price = offer.get('total_premium') or offer.get('price', 0)
            offer_type = offer.get('type', offer.get('coverage_type', 'تأمين'))
            
            # Badge
            badge = ""
            if offer.get("is_cheapest"):
                badge = " 💰 الأرخص"
            elif offer.get("is_recommended"):
                badge = " ⭐ موصى به"
            
            lines.append(f"\n🏢 **العرض {i}: {company}**{badge}")
            lines.append(f"📋 النوع: {offer_type}")
            lines.append(f"💵 السعر الإجمالي: {price:,.2f} ريال")
            
            # المميزات
            features = offer.get('features', []) or offer.get('included_features', [])
            if features:
                lines.append("✅ المميزات:")
                for f in features[:3]:  # أول 3 فقط
                    if isinstance(f, dict):
                        lines.append(f"   {f.get('icon', '•')} {f.get('name', '')}")
                    else:
                        lines.append(f"   • {f}")
        
        lines.append("\n💬 أي عرض يناسبك؟ اختر رقم العرض أو اسم الشركة")
        
        return "\n".join(lines)
    
    def _format_user_history(self, history_info: Dict) -> str:
        """تنسيق سجل المستخدم بشكل احترافي"""
        lines = []
        
        # معلومات الجلسة الحالية
        current = history_info.get('current_session', {})
        if current:
            lines.append("🎯 **الطلب الحالي:**")
            
            if current.get('order_id'):
                lines.append(f"   📋 رقم الطلب: {current['order_id']}")
            
            if current.get('invoice_id'):
                lines.append(f"   🧾 رقم الفاتورة: {current['invoice_id']}")
            
            if current.get('sadad_number'):
                lines.append(f"   💳 رقم السداد: {current['sadad_number']}")
            
            if current.get('policy_id'):
                lines.append(f"   🛡️ رقم الوثيقة: {current['policy_id']}")
                
            if current.get('policy_expiry'):
                lines.append(f"   📅 صالحة حتى: {current['policy_expiry']}")
            
            offer = current.get('selected_offer', {})
            if offer:
                lines.append(f"   🏢 الشركة: {offer.get('company', 'غير محدد')}")
                lines.append(f"   🛡️ التغطية: {offer.get('type', 'غير محدد')}")
                lines.append(f"   💰 السعر: {offer.get('price', 0):,.0f} ريال")
        
        # الوثائق السابقة
        policies = history_info.get('policies', [])
        if policies:
            lines.append("\n📜 **الوثائق السابقة:**")
            for i, policy in enumerate(policies[:5], 1):
                lines.append(f"   {i}. {policy.get('policy_no', 'N/A')} - {policy.get('status', 'غير معروف')}")
        
        return "\n".join(lines) if lines else "لا توجد معلومات متاحة"
    

    async def _handle_resume(
        self,
        context: ConversationContext,
        message: str,
        conversation_id: str,
        phone: Optional[str],
        session_check
    ) -> StageResult:
        """معالجة استئناف الجلسة"""
        
        # تحديد نية المستخدم
        wants_resume = any(w in message for w in ["1", "استمر", "اكمل", "نكمل"])
        wants_new = any(w in message for w in ["2", "جديد", "من البداية", "ابدأ"])
        
        if wants_new:
            clear_history(conversation_id)
            context = await session_manager.create_context(conversation_id, phone)
            
            prompt = "العميل يريد البدء من جديد. رحب به واسأله كيف تقدر تساعده."
            try:
                chat = self.model.start_chat(history=[])
                response = chat.send_message(prompt)
                return StageResult(success=True, response_message=response.text, next_stage=ConversationStage.GREETING)
            except Exception as e:
                return StageResult(success=False, response_message=str(e), error=str(e))
        
        if wants_resume:
            return StageResult(
                success=True,
                response_message="ممتاز! نكمل من حيث توقفنا. كيف أقدر أساعدك؟",
                next_stage=context.current_stage
            )
        
        # عرض رسالة الاستئناف
        hours = session_check.idle_minutes // 60
        mins = session_check.idle_minutes % 60
        time_str = f"{hours} ساعة" if hours > 0 else f"{mins} دقيقة"
        
        stage_info = get_stage_info(context)
        data_summary = get_data_summary(context)
        
        return StageResult(
            success=True,
            response_message=f"""أهلاً بك مجدداً! 👋

لاحظت إنك كنت معانا قبل {time_str}.

📍 كنت في مرحلة: {stage_info['name']}

📋 ما وصلنا له:
{data_summary}

هل تريد:
1️⃣ الاستمرار من حيث توقفت
2️⃣ البدء من جديد""",
            next_stage=ConversationStage.SESSION_RESUME
        )


# Global instance
professional_engine = ProfessionalInsuranceEngine()
