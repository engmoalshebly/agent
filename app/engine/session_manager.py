"""
SAIA Insurance Broker Platform - Session Manager
Handles session resume, timeout, and context preservation
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

from app.core.constants import (
    ConversationStage, 
    SessionStatus,
    SESSION_TIMEOUT_HOURS,
    SESSION_IDLE_TIMEOUT_MINUTES
)

logger = logging.getLogger(__name__)


@dataclass
class SessionCheckResult:
    """Result of session status check"""
    status: SessionStatus
    action: str  # start_new, ask_resume, continue
    last_stage: Optional[ConversationStage] = None
    context_summary: Optional[str] = None
    can_resume: bool = True
    idle_minutes: int = 0


@dataclass
class ConversationContext:
    """Conversation context that persists across messages"""
    conversation_id: str
    user_id: Optional[str] = None
    phone: Optional[str] = None
    current_stage: ConversationStage = ConversationStage.GREETING
    
    # Collected data
    profile_data: Dict[str, Any] = field(default_factory=dict)
    vehicle_data: Dict[str, Any] = field(default_factory=dict)
    
    # Offers and selection
    offers_shown: list = field(default_factory=list)
    selected_offer_id: Optional[int] = None
    selected_offer: Optional[Dict] = None
    
    # Order flow
    order_id: Optional[int] = None
    invoice_id: Optional[int] = None
    policy_id: Optional[int] = None
    
    # Tracking
    last_question: Optional[str] = None
    awaiting_input_type: Optional[str] = None
    retry_count: int = 0
    pending_action: Optional[str] = None  # For confirmation prompts (e.g., "confirm_cancel")
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_message_at: datetime = field(default_factory=datetime.now)

    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "user_id": self.user_id,
            "phone": self.phone,
            "current_stage": self.current_stage.value,
            "profile_data": self.profile_data,
            "vehicle_data": self.vehicle_data,
            "offers_shown": self.offers_shown,
            "selected_offer_id": self.selected_offer_id,
            "order_id": self.order_id,
            "invoice_id": self.invoice_id,
            "policy_id": self.policy_id,
            "last_question": self.last_question,
            "awaiting_input_type": self.awaiting_input_type,
            "retry_count": self.retry_count,
            "pending_action": self.pending_action,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationContext":
        ctx = cls(
            conversation_id=data.get("conversation_id", ""),
            user_id=data.get("user_id"),
            phone=data.get("phone"),
            current_stage=ConversationStage(data.get("current_stage", "greeting")),
            profile_data=data.get("profile_data", {}),
            vehicle_data=data.get("vehicle_data", {}),
            offers_shown=data.get("offers_shown", []),
            selected_offer_id=data.get("selected_offer_id"),
            order_id=data.get("order_id"),
            invoice_id=data.get("invoice_id"),
            policy_id=data.get("policy_id"),
            last_question=data.get("last_question"),
            awaiting_input_type=data.get("awaiting_input_type"),
            retry_count=data.get("retry_count", 0),
            pending_action=data.get("pending_action"),
        )
        return ctx



class SessionManager:
    """
    Manages conversation sessions with resume capability.
    Uses MongoDB for persistent storage.
    """
    
    def __init__(self):
        from app.db.mongodb import mongodb_manager
        self.mg = mongodb_manager
    
    async def _get_collection(self):
        if not self.mg.is_connected():
            await self.mg.connect()
        return self.mg.db.conversation_contexts

    async def check_session(self, conversation_id: str) -> SessionCheckResult:
        """Check session status and determine action."""
        context = await self.get_context(conversation_id)
        
        if not context:
            return SessionCheckResult(status=SessionStatus.NEW, action="start_new")
        
        now = datetime.now()
        idle_time = now - context.last_message_at
        idle_minutes = int(idle_time.total_seconds() / 60)
        
        if idle_time > timedelta(hours=SESSION_TIMEOUT_HOURS):
            return SessionCheckResult(
                status=SessionStatus.EXPIRED,
                action="start_new",
                last_stage=context.current_stage,
                can_resume=False,
                idle_minutes=idle_minutes
            )
        
        if idle_time > timedelta(minutes=SESSION_IDLE_TIMEOUT_MINUTES):
            return SessionCheckResult(
                status=SessionStatus.IDLE,
                action="ask_resume",
                last_stage=context.current_stage,
                context_summary=self._generate_summary(context),
                can_resume=True,
                idle_minutes=idle_minutes
            )
        
        return SessionCheckResult(
            status=SessionStatus.ACTIVE,
            action="continue",
            last_stage=context.current_stage,
            idle_minutes=idle_minutes
        )
    
    async def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Get conversation context from MongoDB"""
        col = await self._get_collection()
        doc = await col.find_one({"conversation_id": conversation_id})
        if doc:
            # Handle datetime parsing from string if necessary, but Moto returns datetime
            if "created_at" in doc and isinstance(doc["created_at"], str):
                doc["created_at"] = datetime.fromisoformat(doc["created_at"])
            if "updated_at" in doc and isinstance(doc["updated_at"], str):
                doc["updated_at"] = datetime.fromisoformat(doc["updated_at"])
            return ConversationContext.from_dict(doc)
        return None
    
    async def create_context(self, conversation_id: str, phone: Optional[str] = None) -> ConversationContext:
        """Create new conversation context in MongoDB"""
        context = ConversationContext(conversation_id=conversation_id, phone=phone)
        col = await self._get_collection()
        await col.replace_one({"conversation_id": conversation_id}, context.to_dict(), upsert=True)
        return context
    
    async def update_context(self, context: ConversationContext):
        """Update conversation context in MongoDB"""
        context.updated_at = datetime.now()
        context.last_message_at = datetime.now()
        col = await self._get_collection()
        await col.replace_one({"conversation_id": context.conversation_id}, context.to_dict(), upsert=True)
    
    async def resume_session(self, conversation_id: str) -> Optional[ConversationContext]:
        """Resume existing session"""
        context = await self.get_context(conversation_id)
        if context:
            await self.update_context(context)
        return context
    
    async def clear_session(self, conversation_id: str):
        """Clear session from MongoDB"""
        col = await self._get_collection()
        await col.delete_one({"conversation_id": conversation_id})
    
    def _generate_summary(self, context: ConversationContext) -> str:
        """Generate human-readable summary of context"""
        parts = []
        
        stage_names = {
            ConversationStage.GREETING: "الترحيب",
            ConversationStage.COLLECTING_PROFILE: "جمع بياناتك",
            ConversationStage.COLLECTING_VEHICLE: "بيانات السيارة",
            ConversationStage.SHOWING_OFFERS: "عرض العروض",
            ConversationStage.AWAITING_SELECTION: "اختيار العرض",
            ConversationStage.CONFIRMATION: "التأكيد",
            ConversationStage.PENDING_PAYMENT: "انتظار الدفع",
        }
        
        stage_name = stage_names.get(context.current_stage, str(context.current_stage.value))
        parts.append(f"المرحلة: {stage_name}")
        
        if context.profile_data:
            parts.append("✓ بياناتك محفوظة")
        
        if context.vehicle_data:
            vehicle_info = context.vehicle_data
            brand = vehicle_info.get("brand", "")
            model = vehicle_info.get("model", "")
            if brand and model:
                parts.append(f"✓ السيارة: {brand} {model}")
        
        if context.selected_offer:
            parts.append("✓ تم اختيار عرض")
        
        return " | ".join(parts)
    
    def generate_resume_message(
        self, 
        check_result: SessionCheckResult,
        context: ConversationContext
    ) -> str:
        """Generate message asking user if they want to resume"""
        
        hours = check_result.idle_minutes // 60
        minutes = check_result.idle_minutes % 60
        
        if hours > 0:
            time_str = f"{hours} ساعة"
            if minutes > 0:
                time_str += f" و {minutes} دقيقة"
        else:
            time_str = f"{minutes} دقيقة"
        
        # Get stage display name
        stage_names = {
            ConversationStage.COLLECTING_PROFILE: "جمع البيانات",
            ConversationStage.COLLECTING_VEHICLE: "بيانات السيارة",
            ConversationStage.SHOWING_OFFERS: "عرض العروض",
            ConversationStage.AWAITING_SELECTION: "اختيار العرض",
            ConversationStage.CONFIRMATION: "التأكيد النهائي",
            ConversationStage.PENDING_PAYMENT: "انتظار الدفع",
        }
        stage_name = stage_names.get(check_result.last_stage, "")
        
        message = f"""أهلاً بك مجدداً! 👋

لاحظت إنك كنت معنا قبل {time_str}"""
        
        if stage_name:
            message += f"\nوصلت لمرحلة \"{stage_name}\""
        
        if check_result.context_summary:
            message += f"\n{check_result.context_summary}"
        
        message += """

تحب نكمل من نفس النقطة؟
1️⃣ نعم، نكمل
2️⃣ لا، أبدأ من جديد"""
        
        return message


# Global instance
session_manager = SessionManager()
