"""
SAIA Insurance Broker Platform - Conversation History Module
إدارة سجل المحادثات
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationMessage:
    """رسالة واحدة في سجل المحادثة"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    stage: str = ""
    data_extracted: Dict[str, Any] = field(default_factory=dict)


class ConversationHistory:
    """
    إدارة سجل المحادثات للسياق
    
    يحتفظ بسجل كامل للرسائل بين المستخدم والنظام
    """
    
    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.messages: List[ConversationMessage] = []
    
    def add_message(
        self,
        role: str,
        content: str,
        stage: str = "",
        data: Optional[Dict] = None
    ):
        """إضافة رسالة جديدة للسجل"""
        self.messages.append(ConversationMessage(
            role=role,
            content=content,
            stage=stage,
            data_extracted=data or {}
        ))
    
    def get_history_text(self, last_n: int = 10) -> str:
        """
        الحصول على النص المنسق للسجل
        مناسب لإرساله للـ LLM
        """
        history = self.messages[-last_n:]
        lines = []
        
        for msg in history:
            role_ar = "🧑 العميل" if msg.role == "user" else "🤖 المساعد"
            lines.append(f"{role_ar}: {msg.content}")
            
            if msg.data_extracted:
                extracted_str = json.dumps(msg.data_extracted, ensure_ascii=False)
                lines.append(f"   [بيانات مستخرجة: {extracted_str}]")
        
        return "\n".join(lines)
    
    def to_gemini_history(self) -> List[Dict]:
        """
        تحويل السجل لصيغة Gemini Chat
        """
        history = []
        for msg in self.messages:
            history.append({
                "role": "user" if msg.role == "user" else "model",
                "parts": [msg.content]
            })
        return history
    
    def get_last_message(self, role: Optional[str] = None) -> Optional[ConversationMessage]:
        """الحصول على آخر رسالة"""
        if not self.messages:
            return None
        
        if role:
            for msg in reversed(self.messages):
                if msg.role == role:
                    return msg
            return None
        
        return self.messages[-1]
    
    def clear(self):
        """مسح السجل"""
        self.messages.clear()
    
    def __len__(self) -> int:
        return len(self.messages)


# تخزين سجلات المحادثات (في الذاكرة)
_conversation_histories: Dict[str, ConversationHistory] = {}


def get_or_create_history(conversation_id: str) -> ConversationHistory:
    """الحصول على سجل المحادثة أو إنشاء جديد"""
    if conversation_id not in _conversation_histories:
        _conversation_histories[conversation_id] = ConversationHistory(conversation_id)
    return _conversation_histories[conversation_id]


def clear_history(conversation_id: str):
    """مسح سجل محادثة معينة"""
    if conversation_id in _conversation_histories:
        del _conversation_histories[conversation_id]


def get_all_conversation_ids() -> List[str]:
    """الحصول على جميع معرفات المحادثات"""
    return list(_conversation_histories.keys())
