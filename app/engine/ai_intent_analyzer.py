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
        
        # تعليمات خاصة بكل مرحلة
        stage_instructions = {
            "greeting": """
في مرحلة GREETING:
⚠️ مهم جداً: إذا ذكر المستخدم نوع تأمين محدد (شامل، ضد الغير، VIP) = intent: "select_service" مع استخراج service_type
- إذا قال "تأمين شامل" أو "ابي شامل" = intent: "select_service", service_type: "comprehensive"
- إذا قال "تأمين ضد الغير" أو "طرف ثالث" = intent: "select_service", service_type: "tpl"
- إذا طلب تأمين بدون تحديد نوع = intent: "ask_services"
- إذا طلب تجديد = intent: "ask_services"
- تحية فقط بدون أي طلب = intent: "greeting"
""",
            "selecting_service": """
في مرحلة SELECTING_SERVICE:
- أي ذكر لـ "شامل" أو "كامل" = intent: "select_service", service_type: "comprehensive"
- أي ذكر لـ "ضد الغير" أو "طرف ثالث" أو "عام" = intent: "select_service", service_type: "tpl"
- أي ذكر لـ "vip" أو "مميز" = intent: "select_service", service_type: "vip"
- إذا أعطى بيانات سيارة = intent: "provide_vehicle_data" واستخرج البيانات
""",
            "collecting_vehicle": """
في مرحلة COLLECTING_VEHICLE:
- استخرج أي معلومات سيارة (brand, model, year, price, plate_no)
- إذا ذكر بيانات سيارة = intent: "provide_vehicle_data"
""",
            "confirming_vehicle": """
في مرحلة CONFIRMING_VEHICLE:
- أي موافقة (نعم، صح، تمام، اوكي، اعتمد، صحيح، موافق، ماشي، زين، يلا، اعتمدها، كمل) = intent: "confirm", confirmation: true
- أي رفض أو تعديل = intent: "modify"
""",
            "showing_offers": """
في مرحلة SHOWING_OFFERS:
- ذكر اسم شركة (ولاء، راجحي، تعاونية، سلامة، ميدغلف، أكسا، تكافل) = intent: "select_offer", company_name: "اسم الشركة"
- ذكر رقم (1، 2، 3، العرض الأول، الثاني) = intent: "select_offer", offer_number: الرقم
- طلب تغيير نوع التأمين = intent: "modify"
""",
            "offer_details": """
في مرحلة OFFER_DETAILS:
- أي موافقة (نعم، تمام، اكمل، موافق، يلا) = intent: "confirm", confirmation: true
- رفض أو تغيير = intent: "modify"
""",
            "collecting_profile": """
في مرحلة COLLECTING_PROFILE:
- استخرج رقم الهوية (10 أرقام تبدأ بـ 1 أو 2) = national_id
- استخرج تاريخ الميلاد = birth_date
- استخرج رقم الجوال (05xxxxxxxx) = phone
""",
            "order_summary": """
في مرحلة ORDER_SUMMARY:
- أي موافقة = intent: "confirm", confirmation: true
- طلب تعديل = intent: "modify"
"""
        }
        
        stage_hint = stage_instructions.get(current_stage.value, "")
        
        prompt = f"""أنت محلل نوايا ذكي لنظام تأمين سيارات سعودي. حلل رسالة المستخدم بدقة.

## المرحلة الحالية: {current_stage.value}

{stage_hint}

## البيانات المجمعة:
{collected_data}

## رسالة المستخدم:
"{message}"

## المطلوب - أرجع JSON فقط:
{{
    "intent": "greeting|ask_services|select_service|provide_profile_data|provide_vehicle_data|select_offer|confirm|reject|cancel|modify|ask_question|unknown",
    "confidence": 0.0-1.0,
    "extracted_data": {{
        "confirmation": true/false إذا كانت موافقة,
        "national_id": "رقم الهوية 10 أرقام",
        "birth_date": "تاريخ الميلاد",
        "phone": "رقم الجوال",
        "service_type": "comprehensive/tpl/vip",
        "service_name": "اسم الخدمة",
        "brand": "ماركة السيارة",
        "model": "موديل السيارة",
        "year": سنة الصنع كرقم,
        "price": قيمة السيارة كرقم,
        "plate_no": "رقم اللوحة",
        "company_name": "اسم شركة التأمين",
        "offer_number": رقم العرض
    }},
    "should_transition": true/false
}}

⚠️ مهم جداً:
- افهم نية المستخدم من السياق حتى لو لم يستخدم كلمات محددة
- استخرج جميع البيانات الموجودة في الرسالة
- أرجع JSON فقط بدون أي نص إضافي"""
        
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

