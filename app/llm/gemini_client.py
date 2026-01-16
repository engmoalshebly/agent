"""
SAIA Insurance Broker Platform - LLM Integration
Gemini AI for intelligent, dynamic responses
"""
import google.generativeai as genai
from typing import Optional, Dict, Any
import logging
import json
import re

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiClient:
    """Gemini LLM Client for intelligent responses"""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self.model = None
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini initialized with model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
    
    async def generate_response(
        self,
        user_message: str,
        context: Dict[str, Any],
        stage: str,
        system_prompt: str = None
    ) -> str:
        """Generate intelligent response using Gemini"""
        
        if not self.model:
            return None
        
        try:
            # Build the prompt
            prompt = self._build_prompt(user_message, context, stage, system_prompt)
            
            # Generate response
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=500,
                )
            )
            
            return response.text
            
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return None
    
    def _build_prompt(
        self,
        user_message: str,
        context: Dict[str, Any],
        stage: str,
        system_prompt: str = None
    ) -> str:
        """Build prompt with context"""
        
        base_prompt = system_prompt or STAGE_PROMPTS.get(stage, DEFAULT_PROMPT)
        
        context_str = json.dumps(context, ensure_ascii=False, indent=2) if context else "{}"
        
        full_prompt = f"""{base_prompt}

=== سياق المحادثة ===
المرحلة الحالية: {stage}
البيانات المجمعة: {context_str}

=== رسالة العميل ===
{user_message}

=== تعليمات إضافية ===
- أجب بالعربية الفصحى البسيطة
- كن ودوداً ومحترفاً
- إذا كان السؤال خارج السياق، أجب بلطف ثم أعد التوجيه
- استخدم الإيموجي باعتدال
- لا تكرر نفس الرد
- افهم نية العميل حتى لو لم يكن واضحاً

الرد:"""
        
        return full_prompt
    
    async def extract_data(
        self,
        user_message: str,
        expected_fields: list
    ) -> Dict[str, Any]:
        """Extract structured data from user message"""
        
        if not self.model:
            return {}
        
        try:
            prompt = f"""استخرج البيانات التالية من رسالة العميل إن وجدت.

الحقول المطلوبة: {', '.join(expected_fields)}

رسالة العميل: "{user_message}"

أرجع النتيجة بصيغة JSON فقط، مثال:
{{"field_name": "value", "field_name2": null}}

إذا لم تجد قيمة، ضع null.
الرد (JSON فقط):"""
            
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', text)
            if json_match:
                return json.loads(json_match.group())
            
            return {}
            
        except Exception as e:
            logger.error(f"Data extraction error: {e}")
            return {}
    
    async def classify_intent(self, user_message: str) -> str:
        """Classify user intent"""
        
        if not self.model:
            return "unknown"
        
        try:
            prompt = f"""صنف نية العميل من الرسالة التالية.

الرسالة: "{user_message}"

الأصناف المتاحة:
- new_insurance: يريد إصدار تأمين جديد
- view_documents: يريد رؤية وثائقه
- track_order: يريد متابعة طلب
- provide_data: يقدم بيانات مطلوبة
- confirm: موافقة أو تأكيد
- reject: رفض أو إلغاء
- question: سؤال عام
- complaint: شكوى
- greeting: تحية
- unclear: غير واضح

أرجع الصنف فقط (كلمة واحدة):"""
            
            response = self.model.generate_content(prompt)
            intent = response.text.strip().lower()
            
            valid_intents = [
                "new_insurance", "view_documents", "track_order",
                "provide_data", "confirm", "reject", "question",
                "complaint", "greeting", "unclear"
            ]
            
            return intent if intent in valid_intents else "unclear"
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "unclear"


# Stage-specific prompts
STAGE_PROMPTS = {
    "greeting": """أنت وكيل مبيعات ودود ومحترف لشركة وسيط تأمين سعودية.
مهمتك: الترحيب بالعميل وفهم ما يريده.

إذا رحب العميل، رحب به واعرض الخيارات:
1️⃣ إصدار تأمين جديد
2️⃣ عرض وثائقي السابقة
3️⃣ متابعة طلب أو فاتورة

إذا سأل سؤالاً عاماً، أجبه ثم اعرض الخيارات.
إذا أهانك، كن محترفاً ولا ترد بالمثل.""",

    "collecting_profile": """أنت تجمع بيانات العميل لإصدار تأمين.

البيانات المطلوبة:
1. رقم الهوية (10 أرقام)
2. تاريخ الميلاد
3. رقم الجوال (اختياري)

قواعد:
- إذا قال "لا يوجد لدي" أو "ما عندي"، اسأله بلطف إذا يريد المساعدة
- إذا أعطى رقم خاطئ، اشرح له الصيغة الصحيحة بلطف
- إذا سأل لماذا تحتاج البيانات، اشرح أنها ضرورية للتأمين
- كن صبوراً ومتفهماً""",

    "collecting_vehicle": """أنت تجمع بيانات سيارة العميل.

البيانات المطلوبة:
- رقم اللوحة أو الرقم التسلسلي
- نوع السيارة (الشركة والموديل)
- سنة الصنع
- القيمة التقديرية

قواعد:
- إذا لم يعرف القيمة، ساعده بتقدير تقريبي
- إذا كتب بطريقة غير واضحة، استخرج ما تستطيع واسأل عن الباقي""",

    "showing_offers": """أنت تعرض عروض التأمين للعميل.

قواعد:
- اشرح الفرق بين العروض إذا سأل
- لا تذكر اسم الشركة
- ساعده في الاختيار حسب احتياجاته
- إذا سأل عن تفاصيل أكثر، قدمها""",

    "confirmation": """العميل في مرحلة التأكيد النهائي.

قواعد:
- إذا تردد، طمئنه
- إذا سأل عن شيء، أجبه
- إذا أراد تعديل، ساعده""",

    "pending_payment": """العميل لديه فاتورة في انتظار الدفع.

قواعد:
- إذا سأل عن طريقة الدفع، اشرح له
- إذا قال "تم الدفع" أو ما شابه، أكد استلام الدفع
- إذا طلب إلغاء، اسأله عن السبب"""
}

DEFAULT_PROMPT = """أنت وكيل مبيعات ذكي ومحترف لشركة وسيط تأمين.

قواعد عامة:
- كن ودوداً ومحترفاً دائماً
- إذا أساء العميل، لا ترد بالمثل
- إذا لم تفهم، اطلب توضيحاً بلطف
- ساعد العميل قدر الإمكان"""


# Global instance
gemini_client = GeminiClient()
