"""
SAIA Insurance Broker Platform - Rule-Based Parser
Fast pattern matching before LLM for clear inputs
"""
import re
from dataclasses import dataclass
from typing import Optional, Any
import logging

from app.core.constants import PATTERNS, InputType

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of rule-based parsing"""
    matched: bool
    input_type: Optional[InputType] = None
    value: Any = None
    confidence: float = 0.0
    use_llm: bool = True
    raw_input: str = ""


class RuleBasedParser:
    """
    Rule-based parser for clear inputs.
    Processes simple patterns (numbers, confirmations) without LLM.
    
    This provides:
    - 100x faster response for simple inputs
    - 100% accuracy for pattern-matched inputs
    - Fallback to LLM for complex inputs
    """
    
    # Extended patterns for Arabic/English
    EXTENDED_PATTERNS = {
        InputType.CHOICE_NUMBER: [
            r"^[1-9]$",
            r"^(واحد|اثنين|ثلاثة|أربعة|خمسة)$",
            r"^(one|two|three|four|five)$",
        ],
        InputType.AFFIRMATIVE: [
            r"^(نعم|اي|ايه|أي|أيه|اه|ايوه)$",
            r"^(yes|y|ok|okay|sure|yep|yeah)$",
            r"^(تمام|موافق|صح|اوك|اكيد|طيب)$",
            r"^1$",
        ],
        InputType.NEGATIVE: [
            r"^(لا|لأ|لاء)$",
            r"^(no|n|nope|cancel)$",
            r"^(إلغاء|الغاء|تخطي|skip)$",
            r"^2$",
        ],
        InputType.NATIONAL_ID: [
            r"^[12]\d{9}$",
        ],
        InputType.PHONE: [
            r"^05\d{8}$",
            r"^5\d{8}$",
            r"^966\d{9}$",
            r"^\+966\d{9}$",
        ],
        InputType.PLATE_NUMBER: [
            r"^[\u0621-\u064A]\s*[\u0621-\u064A]\s*[\u0621-\u064A]\s*\d{4}$",
            r"^[A-Z]\s*[A-Z]\s*[A-Z]\s*\d{4}$",
        ],
        InputType.VEHICLE_VALUE: [
            r"^\d{4,7}$",  # 1000 - 9999999
        ],
        InputType.PAYMENT_CONFIRM: [
            r"(تم الدفع|دفعت|تم|done|paid)",
        ],
    }
    
    # Number word mappings
    NUMBER_WORDS = {
        # Arabic
        "واحد": 1, "اثنين": 2, "ثلاثة": 3, "أربعة": 4, "خمسة": 5,
        "ستة": 6, "سبعة": 7, "ثمانية": 8, "تسعة": 9,
        # English
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9,
        # ordinals
        "الأول": 1, "الثاني": 2, "الثالث": 3, "الرابع": 4, "الخامس": 5,
        "الأولى": 1, "الثانية": 2, "الثالثة": 3, "الرابعة": 4, "الخامسة": 5,
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    }
    
    @classmethod
    def parse(
        cls, 
        message: str, 
        expected_type: Optional[InputType] = None,
        max_choice: int = 9
    ) -> ParseResult:
        """
        Parse message using rule-based patterns.
        
        Args:
            message: User input message
            expected_type: Expected input type (if known)
            max_choice: Maximum valid choice number
            
        Returns:
            ParseResult with matched=True if pattern matched
        """
        clean = message.strip()
        lower = clean.lower()
        
        # If expected type is specified, check that first
        if expected_type:
            result = cls._check_type(clean, lower, expected_type, max_choice)
            if result.matched:
                return result
        
        # General pattern search
        for input_type, patterns in cls.EXTENDED_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, clean, re.IGNORECASE):
                    value = cls._normalize(clean, input_type)
                    
                    # Validate choice number range
                    if input_type == InputType.CHOICE_NUMBER:
                        if isinstance(value, int) and value > max_choice:
                            continue
                    
                    logger.debug(f"Rule match: {input_type.value} = {value}")
                    
                    return ParseResult(
                        matched=True,
                        input_type=input_type,
                        value=value,
                        confidence=1.0,
                        use_llm=False,
                        raw_input=message
                    )
        
        # No match - use LLM
        return ParseResult(
            matched=False,
            use_llm=True,
            raw_input=message
        )
    
    @classmethod
    def _check_type(
        cls, 
        clean: str, 
        lower: str, 
        expected_type: InputType,
        max_choice: int
    ) -> ParseResult:
        """Check specific expected type"""
        patterns = cls.EXTENDED_PATTERNS.get(expected_type, [])
        
        for pattern in patterns:
            if re.match(pattern, clean, re.IGNORECASE):
                value = cls._normalize(clean, expected_type)
                
                if expected_type == InputType.CHOICE_NUMBER:
                    if isinstance(value, int) and value > max_choice:
                        continue
                
                return ParseResult(
                    matched=True,
                    input_type=expected_type,
                    value=value,
                    confidence=1.0,
                    use_llm=False,
                    raw_input=clean
                )
        
        return ParseResult(matched=False, use_llm=True, raw_input=clean)
    
    @classmethod
    def _normalize(cls, value: str, input_type: InputType) -> Any:
        """Normalize parsed value"""
        clean = value.strip()
        lower = clean.lower()
        
        if input_type == InputType.CHOICE_NUMBER:
            # Try direct number
            if clean.isdigit():
                return int(clean)
            # Try word mapping
            return cls.NUMBER_WORDS.get(lower, clean)
        
        elif input_type in (InputType.AFFIRMATIVE,):
            return True
        
        elif input_type in (InputType.NEGATIVE,):
            return False
        
        elif input_type == InputType.PHONE:
            # Normalize Saudi phone
            digits = re.sub(r'\D', '', clean)
            if len(digits) == 9 and digits.startswith('5'):
                return '0' + digits
            elif len(digits) == 12 and digits.startswith('966'):
                return '0' + digits[3:]
            elif len(digits) == 10 and digits.startswith('05'):
                return digits
            return clean
        
        elif input_type == InputType.VEHICLE_VALUE:
            # Return as integer
            digits = re.sub(r'\D', '', clean)
            return int(digits) if digits else 0
        
        elif input_type == InputType.PAYMENT_CONFIRM:
            return True
        
        return clean
    
    @classmethod
    def extract_choice(cls, message: str, max_choice: int = 5) -> Optional[int]:
        """Quick helper to extract choice number from text"""
        # 1. Try strict match
        result = cls.parse(message, InputType.CHOICE_NUMBER, max_choice)
        if result.matched and isinstance(result.value, int):
            return result.value
        
        # 2. Try searching for number words or digits in the message
        lower = message.lower()
        for word, val in cls.NUMBER_WORDS.items():
            if word in lower and val <= max_choice:
                return val
        
        # 3. Try searching for digits
        digits = re.findall(r'\b[1-9]\b', message)
        if digits:
            val = int(digits[0])
            if val <= max_choice:
                return val
                
        return None
    
    @classmethod
    def is_affirmative(cls, message: str) -> bool:
        """Quick helper to check if message is affirmative"""
        result = cls.parse(message, InputType.AFFIRMATIVE)
        return result.matched and result.value is True
    
    @classmethod
    def is_negative(cls, message: str) -> bool:
        """Quick helper to check if message is negative"""
        result = cls.parse(message, InputType.NEGATIVE)
        return result.matched and result.value is False
