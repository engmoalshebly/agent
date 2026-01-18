"""
AI Intent Analyzer - تحليل نية المستخدم بالذكاء الاصطناعي
يستبدل جميع الكلمات الثابتة بتحليل ذكي
"""
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

import google.generativeai as genai
from app.config import settings
from app.core.constants import ConversationStage

logger = logging.getLogger(__name__)


class UserIntent(str, Enum):
    """أنواع نوايا المستخدم"""
    GREETING = "greeting"
    ASK_SERVICES = "ask_services"
    SELECT_SERVICE = "select_service"
    PROVIDE_PROFILE_DATA = "provide_profile_data"
    PROVIDE_VEHICLE_DATA = "provide_vehicle_data"
    SELECT_OFFER = "select_offer"
    CONFIRM = "confirm"
    REJECT = "reject"
    CANCEL = "cancel"
    MODIFY = "modify"
    ASK_QUESTION = "ask_question"
    ASK_HISTORY = "ask_history"  # استعلام عن السجل
    RESUME = "resume"
    UNKNOWN = "unknown"


@dataclass
class IntentAnalysisResult:
    """نتيجة تحليل النية"""
    intent: UserIntent
    confidence: float
    extracted_data: Dict[str, Any]
    should_transition: bool
    next_stage: Optional[ConversationStage]
    response_hint: str
    raw_response: str = ""


class AIIntentAnalyzer:
    """محلل النية الذكي باستخدام Gemini"""
    
    def __init__(self):
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """Initialize Gemini model"""
        try:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    settings.GEMINI_MODEL,
                    generation_config=genai.GenerationConfig(
                        temperature=0.2,  # Lower for more consistent analysis
                        max_output_tokens=500,
                    )
                )
                logger.info("✅ AI Intent Analyzer initialized")
        except Exception as e:
            logger.error(f"AI Intent Analyzer init error: {e}")
    
    def analyze(
        self,
        message: str,
        current_stage: ConversationStage,
        context_data: Dict[str, Any],
        available_services: List[Dict] = None
    ) -> IntentAnalysisResult:
        """
        تحليل نية المستخدم بالذكاء الاصطناعي
        
        Args:
            message: رسالة المستخدم
            current_stage: المرحلة الحالية
            context_data: البيانات المجمعة
            available_services: الخدمات المتوفرة من DB
        """
        if not self.model:
            return self._fallback_analysis(message, current_stage)
        
        try:
            prompt = self._build_analysis_prompt(
                message, current_stage, context_data, available_services
            )
            
            response = self.model.generate_content(prompt)
            result = self._parse_response(response.text, message, current_stage)
            
            logger.info(f"🧠 AI Intent: {result.intent.value} (confidence: {result.confidence})")
            return result
            
        except Exception as e:
            logger.error(f"AI analysis error: {e}")
            return self._fallback_analysis(message, current_stage)
    
    def _build_analysis_prompt(
        self,
        message: str,
        current_stage: ConversationStage,
        context_data: Dict,
        available_services: List[Dict] = None
    ) -> str:
        """بناء prompt محسن لتحليل النية"""
        
        services_text = ""
        if available_services:
            services_text = "\n".join([
                f"- {s.get('name_ar', s.get('code', ''))}: {s.get('description', '')}"
                for s in available_services
            ])
        
        collected_data = json.dumps(context_data, ensure_ascii=False, default=str)
        
        # تعليمات ذكية بناءً على المرحلة (بدون كلمات محددة)
        stage_context = {
            "greeting": "المستخدم في بداية المحادثة. قد يحيي، يسأل عن الخدمات، أو يطلب تأمين مباشرة.",
            "selecting_service": "المستخدم يختار نوع التأمين (شامل/ضد الغير/VIP).",
            "collecting_vehicle": "جمع بيانات السيارة (النوع، الموديل، السنة، القيمة، اللوحة).",
            "confirming_vehicle": "المستخدم يؤكد أو يعدل بيانات السيارة المعروضة.",
            "showing_offers": "عرض العروض للمستخدم. ينتظر اختيار عرض برقم أو اسم شركة.",
            "offer_details": "تفاصيل العرض المختار. ينتظر موافقة أو رفض.",
            "collecting_profile": "جمع البيانات الشخصية (الهوية، تاريخ الميلاد، الجوال).",
            "order_summary": "ملخص الطلب الكامل. ينتظر التأكيد النهائي."
        }
        
        stage_desc = stage_context.get(current_stage.value, "مرحلة غير محددة")
        
        prompt = f"""أنت محلل نوايا ذكي جداً لنظام تأمين سيارات سعودي.
مهمتك: فهم نية المستخدم الحقيقية من رسالته وتصنيفها بدقة.

═══════════════════════════════════════
📍 السياق الحالي
═══════════════════════════════════════
• المرحلة: {current_stage.value}
• الوصف: {stage_desc}
• البيانات المجمعة: {collected_data}

═══════════════════════════════════════
💬 رسالة المستخدم
═══════════════════════════════════════
"{message}"

═══════════════════════════════════════
🧠 تصنيفات النوايا (حلل المعنى وليس الكلمات!)
═══════════════════════════════════════

1. **greeting** - المستخدم يُلقي تحية فقط بدون طلب
2. **ask_services** - يسأل عن الخدمات المتاحة أو أنواع التأمين
3. **select_service** - يختار نوع تأمين (شامل/ضد الغير/VIP)
4. **provide_vehicle_data** - يقدم معلومات عن سيارته
5. **provide_profile_data** - يقدم بياناته الشخصية (هوية/ميلاد/جوال)
6. **select_offer** - يختار عرضاً من العروض المعروضة
7. **confirm** - يوافق ويريد المتابعة
8. **reject** - يرفض العرض الحالي
9. **cancel** - يريد إلغاء العملية أو الخروج أو عدم الاستمرار
10. **modify** - يريد تعديل بيانات أو تغيير اختيار سابق
11. **ask_history** - يسأل عن سجله أو وثائقه أو تأميناته السابقة
12. **ask_question** - لديه سؤال عام أو استفسار
13. **resume** - يريد استئناف طلب سابق
14. **unknown** - لا يمكن تحديد النية

═══════════════════════════════════════
🎯 قواعد التحليل الذكي
═══════════════════════════════════════

✅ افهم **المعنى العام** للرسالة وليس كلمات بعينها
✅ انتبه لـ **نبرة** الرسالة (إيجابية/سلبية/محايدة)
✅ إذا المستخدم يُعبر عن **عدم الرغبة** أو **الرفض** = cancel
✅ إذا المستخدم يُعبر عن **الموافقة** أو **القبول** = confirm
✅ إذا المستخدم يسأل عن **معلومات سابقة** له = ask_history
✅ استخرج **كل البيانات** الموجودة في الرسالة

⛔ لا تعتمد على كلمات محددة - افهم السياق!
⛔ "لا اريد" في سياق رفض = cancel (وليس confirm)
⛔ "نعم" في سياق تأكيد = confirm
⛔ أرقام في سياق اختيار عرض = select_offer

═══════════════════════════════════════
📤 أرجع JSON فقط:
═══════════════════════════════════════
{{
    "intent": "اختر من القائمة أعلاه",
    "confidence": 0.0-1.0,
    "reasoning": "شرح مختصر للتحليل",
    "extracted_data": {{
        "confirmation": true/false,
        "national_id": "رقم الهوية إن وجد",
        "birth_date": "تاريخ الميلاد إن وجد",
        "phone": "رقم الجوال إن وجد",
        "service_type": "comprehensive/tpl/vip",
        "brand": "ماركة السيارة",
        "model": "موديل السيارة",
        "year": سنة كرقم,
        "price": قيمة كرقم,
        "plate_no": "رقم اللوحة",
        "company_name": "اسم الشركة",
        "offer_number": رقم العرض
    }},
    "should_transition": true/false
}}

أرجع JSON فقط بدون أي نص إضافي."""
        
        return prompt
    
    def _parse_response(
        self,
        response_text: str,
        message: str,
        current_stage: ConversationStage
    ) -> IntentAnalysisResult:
        """تحليل استجابة الـ AI"""
        try:
            # Clean response
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            data = json.loads(text)
            
            # Parse intent
            intent_str = data.get("intent", "unknown")
            try:
                intent = UserIntent(intent_str)
            except ValueError:
                intent = UserIntent.UNKNOWN
            
            # Parse next stage
            next_stage = None
            next_stage_str = data.get("next_stage")
            if next_stage_str:
                try:
                    next_stage = ConversationStage(next_stage_str)
                except ValueError:
                    pass
            
            # Clean extracted data (remove None values)
            extracted = data.get("extracted_data", {})
            extracted = {k: v for k, v in extracted.items() if v is not None and v != ""}
            
            return IntentAnalysisResult(
                intent=intent,
                confidence=float(data.get("confidence", 0.5)),
                extracted_data=extracted,
                should_transition=data.get("should_transition", False),
                next_stage=next_stage,
                response_hint=data.get("response_hint", ""),
                raw_response=response_text
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return self._fallback_analysis(message, current_stage)
    
    def _fallback_analysis(
        self,
        message: str,
        current_stage: ConversationStage
    ) -> IntentAnalysisResult:
        """
        تحليل احتياطي بسيط - يستخدم فقط في حالة فشل الـ AI
        لا يوجد كلمات ثابتة - النظام يعتمد 100% على الـ AI
        """
        return IntentAnalysisResult(
            intent=UserIntent.UNKNOWN,
            confidence=0.3,
            extracted_data={},
            should_transition=False,
            next_stage=None,
            response_hint=""
        )


# Singleton instance
ai_intent_analyzer = AIIntentAnalyzer()

