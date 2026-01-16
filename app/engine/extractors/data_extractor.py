"""
SAIA Insurance Broker Platform - Stage-Aware AI Data Extraction
استخراج البيانات الذكي حسب المرحلة

الميزات:
- يعرف المرحلة الحالية
- يعرف الهيكلية المطلوبة لكل مرحلة
- يستخرج البيانات الموجودة
- يحدد البيانات الناقصة
- يرجع كل شيء بهيكلية موحدة
"""
import json
import re
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
import google.generativeai as genai

from app.config import settings
from app.core.constants import ConversationStage

logger = logging.getLogger(__name__)


# =============================================
# هيكلية البيانات لكل مرحلة
# =============================================
STAGE_SCHEMAS = {
    ConversationStage.GREETING: {
        "fields": [],  # لا يوجد بيانات مطلوبة
        "description": "الترحيب والدردشة"
    },
    
    ConversationStage.SELECTING_SERVICE: {
        "fields": [
            {"name": "service_type", "type": "string", "required": True, 
             "options": ["tpl", "comprehensive", "vip"],
             "description": "نوع التأمين: tpl=ضد الغير، comprehensive=شامل، vip=VIP"}
        ],
        "description": "اختيار نوع التأمين"
    },
    
    ConversationStage.COLLECTING_VEHICLE: {
        "fields": [
            {"name": "brand", "type": "string", "required": True, 
             "description": "ماركة السيارة مثل: تويوتا، هيونداي، نيسان"},
            {"name": "model", "type": "string", "required": False, 
             "description": "موديل السيارة مثل: كامري، سوناتا، التيما"},
            {"name": "year", "type": "integer", "required": True, 
             "description": "سنة الصنع (2000-2030)"},
            {"name": "value", "type": "number", "required": True, 
             "description": "قيمة السيارة بالريال"},
            {"name": "plate_no", "type": "string", "required": True, 
             "description": "رقم اللوحة (حروف وأرقام)"}
        ],
        "description": "جمع بيانات السيارة"
    },
    
    ConversationStage.CONFIRMING_VEHICLE: {
        "fields": [
            {"name": "confirmation", "type": "boolean", "required": True,
             "description": "هل المستخدم يوافق؟ true/false"}
        ],
        "description": "تأكيد بيانات السيارة"
    },
    
    ConversationStage.SHOWING_OFFERS: {
        "fields": [
            {"name": "offer_number", "type": "integer", "required": False,
             "description": "رقم العرض المختار (1، 2، 3...)"},
            {"name": "company_name", "type": "string", "required": False,
             "description": "اسم شركة التأمين المختارة"}
        ],
        "description": "اختيار عرض التأمين"
    },
    
    ConversationStage.COLLECTING_PROFILE: {
        "fields": [
            {"name": "national_id", "type": "string", "required": True,
             "description": "رقم الهوية الوطنية (10 أرقام يبدأ بـ 1 أو 2)"},
            {"name": "birth_date", "type": "string", "required": True,
             "description": "تاريخ الميلاد بصيغة YYYY-MM-DD"},
            {"name": "phone", "type": "string", "required": False,
             "description": "رقم الجوال (يبدأ بـ 05)"}
        ],
        "description": "جمع البيانات الشخصية"
    },
    
    ConversationStage.ORDER_SUMMARY: {
        "fields": [
            {"name": "confirmation", "type": "boolean", "required": True,
             "description": "تأكيد الطلب النهائي"}
        ],
        "description": "تأكيد الطلب"
    },
    
    ConversationStage.CONFIRMATION: {
        "fields": [
            {"name": "confirmation", "type": "boolean", "required": True,
             "description": "التأكيد النهائي"}
        ],
        "description": "التأكيد النهائي"
    },
    
    ConversationStage.PENDING_PAYMENT: {
        "fields": [
            {"name": "payment_confirmed", "type": "boolean", "required": True,
             "description": "هل تم الدفع؟"}
        ],
        "description": "تأكيد الدفع"
    }
}


@dataclass
class ExtractionResult:
    """نتيجة استخراج البيانات"""
    extracted: Dict[str, Any] = field(default_factory=dict)  # البيانات المستخرجة
    missing: List[str] = field(default_factory=list)         # الحقول الناقصة المطلوبة
    optional_missing: List[str] = field(default_factory=list)  # الحقول الاختيارية الناقصة
    is_complete: bool = False                                 # هل اكتملت البيانات المطلوبة؟
    stage: str = ""                                          # المرحلة الحالية
    raw_response: str = ""                                   # رد AI الخام
    
    def to_dict(self) -> Dict:
        return asdict(self)


class StageAwareDataExtractor:
    """
    مستخرج بيانات ذكي حسب المرحلة
    
    - يعرف المرحلة الحالية
    - يعرف ما يجب استخراجه
    - يرجع البيانات + الناقص
    """
    
    def __init__(self):
        self.model = None
        self.logger = logging.getLogger(__name__)
        self._init_model()
    
    def _init_model(self):
        """تهيئة Gemini"""
        try:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.model = genai.GenerativeModel(
                    "gemini-2.0-flash-lite",
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        max_output_tokens=500,
                    )
                )
                self.logger.info("✅ Stage-Aware Data Extractor initialized")
        except Exception as e:
            self.logger.error(f"❌ Extractor init error: {e}")
    
    def extract_all(self, message: str, stage: ConversationStage = None) -> Dict[str, Any]:
        """
        استخراج البيانات (للتوافق مع الكود القديم)
        يرجع Dict بسيط
        """
        result = self.extract_for_stage(message, stage)
        return result.extracted
    
    def extract_for_stage(
        self, 
        message: str, 
        stage: ConversationStage = None,
        existing_data: Dict[str, Any] = None
    ) -> ExtractionResult:
        """
        استخراج البيانات حسب المرحلة
        
        Args:
            message: رسالة المستخدم
            stage: المرحلة الحالية
            existing_data: البيانات الموجودة مسبقاً
            
        Returns:
            ExtractionResult مع البيانات المستخرجة والناقصة
        """
        result = ExtractionResult(stage=stage.value if stage else "unknown")
        
        if not message or len(message.strip()) < 2:
            return result
        
        # الحصول على هيكلية المرحلة
        schema = STAGE_SCHEMAS.get(stage, {"fields": [], "description": ""})
        
        # استخراج باستخدام AI
        ai_data = self._extract_with_ai(message, stage, schema)
        
        # دمج مع fallback
        fallback_data = self._extract_fallback(message)
        result.extracted = {**fallback_data, **ai_data}
        
        # تحديد الحقول الناقصة
        existing = existing_data or {}
        for field_info in schema.get("fields", []):
            field_name = field_info["name"]
            
            # هل الحقل موجود في المستخرج أو الموجود مسبقاً؟
            has_value = field_name in result.extracted or field_name in existing
            
            if not has_value:
                if field_info.get("required", False):
                    result.missing.append(field_name)
                else:
                    result.optional_missing.append(field_name)
        
        # هل اكتملت البيانات المطلوبة؟
        result.is_complete = len(result.missing) == 0
        
        self.logger.info(f"📊 Stage: {stage}, Extracted: {list(result.extracted.keys())}, Missing: {result.missing}")
        
        return result
    
    def _build_extraction_prompt(
        self, 
        message: str, 
        stage: ConversationStage,
        schema: Dict
    ) -> str:
        """بناء برومبت الاستخراج حسب المرحلة"""
        
        # بناء وصف الحقول
        fields_desc = []
        for f in schema.get("fields", []):
            req = "مطلوب" if f.get("required") else "اختياري"
            fields_desc.append(f"- {f['name']} ({f['type']}) [{req}]: {f['description']}")
        
        fields_text = "\n".join(fields_desc) if fields_desc else "لا توجد حقول محددة"
        
        prompt = f"""أنت مستخرج بيانات دقيق. المرحلة الحالية: {stage.value}

# المرحلة: {schema.get('description', stage.value)}

# الحقول المطلوب استخراجها:
{fields_text}

# القواعد:
1. استخرج فقط الحقول المذكورة أعلاه
2. أرجع JSON فقط بدون أي نص
3. لا تضع حقل إذا لم تجده في الرسالة
4. افهم اللهجة السعودية

# تحويلات مهمة:
- "شامل" → service_type: "comprehensive"
- "ضد الغير" → service_type: "tpl"
- "VIP" → service_type: "vip"
- "نعم/اوكي/تمام/موافق/اعتمد" → confirmation: true
- "لا/الغي" → confirmation: false
- "الراجحي" → company_name: "الراجحي"
- "التعاونية" → company_name: "التعاونية"

# رسالة المستخدم:
{message}

# أرجع JSON فقط:
"""
        return prompt
    
    def _extract_with_ai(
        self, 
        message: str, 
        stage: ConversationStage,
        schema: Dict
    ) -> Dict[str, Any]:
        """استخراج باستخدام AI"""
        if not self.model or not stage:
            return {}
        
        try:
            prompt = self._build_extraction_prompt(message, stage, schema)
            response = self.model.generate_content(prompt)
            
            text = response.text.strip()
            
            # تنظيف markdown
            if text.startswith("```"):
                text = re.sub(r'^```\w*\n?', '', text)
                text = re.sub(r'\n?```$', '', text)
            
            data = json.loads(text)
            return self._validate_and_convert(data, schema)
            
        except Exception as e:
            self.logger.debug(f"AI extraction error: {e}")
            return {}
    
    def _validate_and_convert(self, data: Dict, schema: Dict) -> Dict[str, Any]:
        """التحقق من البيانات وتحويل الأنواع"""
        result = {}
        
        for field_info in schema.get("fields", []):
            field_name = field_info["name"]
            field_type = field_info.get("type", "string")
            
            if field_name not in data:
                continue
            
            value = data[field_name]
            
            # تحويل حسب النوع
            try:
                if field_type == "integer":
                    result[field_name] = int(value)
                elif field_type == "number":
                    val_str = str(value).replace(",", "").replace("،", "")
                    result[field_name] = float(val_str)
                    # للتوافق مع الكود القديم
                    if field_name == "value":
                        result["price"] = result[field_name]
                elif field_type == "boolean":
                    result[field_name] = bool(value)
                else:
                    result[field_name] = str(value).strip()
            except (ValueError, TypeError):
                pass
        
        # التعامل مع حقول إضافية ليست في الـ schema
        for key in ["confirmation", "service_type", "company_name"]:
            if key in data and key not in result:
                result[key] = data[key]
        
        return result
    
    def _extract_fallback(self, message: str) -> Dict[str, Any]:
        """استخراج بسيط كـ fallback"""
        result = {}
        
        # السنة
        year_match = re.search(r'\b(20[0-2]\d)\b', message)
        if year_match:
            year = int(year_match.group(1))
            if 2010 <= year <= 2026:
                result["year"] = year
        
        # القيمة
        for pattern in [r'(\d{1,3}(?:[,،]\d{3})*)\s*ريال', r'قيمت?ها?\s*[:=]?\s*(\d+)']:
            match = re.search(pattern, message)
            if match:
                val = match.group(1).replace(",", "").replace("،", "")
                try:
                    result["price"] = float(val)
                    result["value"] = result["price"]
                    break
                except ValueError:
                    pass
        
        # اللوحة
        plate_match = re.search(r'([ا-ي]\s*[ا-ي]\s*[ا-ي])\s*(\d{1,4})', message)
        if plate_match:
            result["plate_no"] = f"{plate_match.group(1).replace(' ', '')} {plate_match.group(2)}"
        
        # الهوية
        id_match = re.search(r'\b([12]\d{9})\b', message)
        if id_match:
            result["national_id"] = id_match.group(1)
        
        # التأكيد
        if any(w in message for w in ["نعم", "اوكي", "تمام", "موافق", "اعتمد", "صحيح"]):
            result["confirmation"] = True
        if any(w in message for w in ["لا", "الغي", "ما ابي"]):
            result["confirmation"] = False
        
        # نوع الخدمة
        if "شامل" in message:
            result["service_type"] = "comprehensive"
        elif "ضد الغير" in message or "طرف ثالث" in message:
            result["service_type"] = "tpl"
        elif "vip" in message.lower():
            result["service_type"] = "vip"
        
        # اسم الشركة
        companies = {
            "راجحي": "الراجحي", "تعاونية": "التعاونية", 
            "ميدغلف": "ميدغلف", "ولاء": "ولاء", "سلامة": "سلامة"
        }
        for key, val in companies.items():
            if key in message:
                result["company_name"] = val
                break
        
        return result


# Global instance
data_extractor = StageAwareDataExtractor()
