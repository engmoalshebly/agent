"""
SAIA Insurance Broker Platform - State Machine
Defines conversation states and transitions
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Any
import logging

from app.core.constants import ConversationStage

logger = logging.getLogger(__name__)


@dataclass
class StageTransition:
    """Defines a valid transition between stages"""
    from_stage: ConversationStage
    to_stage: ConversationStage
    condition: Optional[str] = None
    description: str = ""


class ConversationStateMachine:
    """
    State machine for conversation flow.
    
    Defines valid transitions and ensures proper flow.
    """
    
    # Define all valid transitions
    TRANSITIONS: List[StageTransition] = [
        # Session management
        StageTransition(ConversationStage.SESSION_CHECK, ConversationStage.GREETING, "new_session"),
        StageTransition(ConversationStage.SESSION_CHECK, ConversationStage.SESSION_RESUME, "idle_session"),
        StageTransition(ConversationStage.SESSION_RESUME, ConversationStage.GREETING, "start_fresh"),
        StageTransition(ConversationStage.SESSION_RESUME, ConversationStage.COLLECTING_PROFILE, "resume_profile"),
        StageTransition(ConversationStage.SESSION_RESUME, ConversationStage.COLLECTING_VEHICLE, "resume_vehicle"),
        StageTransition(ConversationStage.SESSION_RESUME, ConversationStage.SHOWING_OFFERS, "resume_offers"),
        StageTransition(ConversationStage.SESSION_RESUME, ConversationStage.PENDING_PAYMENT, "resume_payment"),
        
        # Main flow
        StageTransition(ConversationStage.GREETING, ConversationStage.COLLECTING_PROFILE, "new_insurance"),
        StageTransition(ConversationStage.GREETING, ConversationStage.DOCUMENTS_VIEW, "view_documents"),
        StageTransition(ConversationStage.GREETING, ConversationStage.ORDER_TRACKING, "track_order"),
        
        # Profile to Vehicle
        StageTransition(ConversationStage.COLLECTING_PROFILE, ConversationStage.COLLECTING_VEHICLE, "profile_complete"),
        StageTransition(ConversationStage.COLLECTING_PROFILE, ConversationStage.COLLECTING_PROFILE, "profile_incomplete"),
        
        # Vehicle flow
        StageTransition(ConversationStage.COLLECTING_VEHICLE, ConversationStage.ASK_ANOTHER_VEHICLE, "vehicle_complete"),
        StageTransition(ConversationStage.COLLECTING_VEHICLE, ConversationStage.COLLECTING_VEHICLE, "vehicle_incomplete"),
        StageTransition(ConversationStage.ASK_ANOTHER_VEHICLE, ConversationStage.COLLECTING_VEHICLE, "add_another"),
        StageTransition(ConversationStage.ASK_ANOTHER_VEHICLE, ConversationStage.FETCHING_OFFERS, "no_more_vehicles"),
        
        # Offers flow
        StageTransition(ConversationStage.FETCHING_OFFERS, ConversationStage.SHOWING_OFFERS, "offers_found"),
        StageTransition(ConversationStage.FETCHING_OFFERS, ConversationStage.ERROR, "no_offers"),
        StageTransition(ConversationStage.SHOWING_OFFERS, ConversationStage.AWAITING_SELECTION, "offers_shown"),
        StageTransition(ConversationStage.AWAITING_SELECTION, ConversationStage.CONFIRMATION, "offer_selected"),
        StageTransition(ConversationStage.AWAITING_SELECTION, ConversationStage.AWAITING_SELECTION, "invalid_selection"),
        
        # Confirmation flow
        StageTransition(ConversationStage.CONFIRMATION, ConversationStage.CREATING_INVOICE, "confirmed"),
        StageTransition(ConversationStage.CONFIRMATION, ConversationStage.COLLECTING_PROFILE, "edit_profile"),
        StageTransition(ConversationStage.CONFIRMATION, ConversationStage.COLLECTING_VEHICLE, "edit_vehicle"),
        StageTransition(ConversationStage.CONFIRMATION, ConversationStage.GREETING, "canceled"),
        
        # Invoice and payment
        StageTransition(ConversationStage.CREATING_INVOICE, ConversationStage.PENDING_PAYMENT, "invoice_created"),
        StageTransition(ConversationStage.PENDING_PAYMENT, ConversationStage.ISSUING_POLICY, "payment_confirmed"),
        StageTransition(ConversationStage.PENDING_PAYMENT, ConversationStage.ERROR, "invoice_expired"),
        
        # Policy issuance
        StageTransition(ConversationStage.ISSUING_POLICY, ConversationStage.ASK_INSURE_ANOTHER, "policy_issued"),
        StageTransition(ConversationStage.ASK_INSURE_ANOTHER, ConversationStage.COLLECTING_VEHICLE, "insure_another"),
        StageTransition(ConversationStage.ASK_INSURE_ANOTHER, ConversationStage.DONE, "finish"),
        
        # Special flows
        StageTransition(ConversationStage.DOCUMENTS_VIEW, ConversationStage.GREETING, "back_to_menu"),
        StageTransition(ConversationStage.ORDER_TRACKING, ConversationStage.GREETING, "back_to_menu"),
        StageTransition(ConversationStage.ERROR, ConversationStage.GREETING, "retry"),
        StageTransition(ConversationStage.ERROR, ConversationStage.HANDOFF_HUMAN, "need_human"),
    ]
    
    @classmethod
    def get_valid_transitions(cls, from_stage: ConversationStage) -> List[StageTransition]:
        """Get all valid transitions from a stage"""
        return [t for t in cls.TRANSITIONS if t.from_stage == from_stage]
    
    @classmethod
    def can_transition(cls, from_stage: ConversationStage, to_stage: ConversationStage) -> bool:
        """Check if transition is valid"""
        return any(
            t.from_stage == from_stage and t.to_stage == to_stage 
            for t in cls.TRANSITIONS
        )
    
    @classmethod
    def get_next_stages(cls, current_stage: ConversationStage) -> List[ConversationStage]:
        """Get possible next stages from current"""
        return [t.to_stage for t in cls.get_valid_transitions(current_stage)]
    
    @classmethod
    def validate_transition(cls, from_stage: ConversationStage, to_stage: ConversationStage) -> bool:
        """Validate and log transition"""
        if cls.can_transition(from_stage, to_stage):
            logger.debug(f"Valid transition: {from_stage.value} -> {to_stage.value}")
            return True
        
        logger.warning(f"Invalid transition attempted: {from_stage.value} -> {to_stage.value}")
        return False


@dataclass
class StageHandler:
    """Configuration for a stage handler"""
    stage: ConversationStage
    prompt_template: str
    expected_input: Optional[str] = None
    required_fields: List[str] = None
    next_stage_success: Optional[ConversationStage] = None
    next_stage_failure: Optional[ConversationStage] = None


# Stage handlers configuration
STAGE_HANDLERS: Dict[ConversationStage, StageHandler] = {
    ConversationStage.GREETING: StageHandler(
        stage=ConversationStage.GREETING,
        prompt_template="greeting",
        expected_input="choice_number",
        next_stage_success=ConversationStage.COLLECTING_PROFILE
    ),
    ConversationStage.COLLECTING_PROFILE: StageHandler(
        stage=ConversationStage.COLLECTING_PROFILE,
        prompt_template="collecting_profile",
        required_fields=["national_id", "birth_date"],
        next_stage_success=ConversationStage.COLLECTING_VEHICLE
    ),
    ConversationStage.COLLECTING_VEHICLE: StageHandler(
        stage=ConversationStage.COLLECTING_VEHICLE,
        prompt_template="collecting_vehicle",
        required_fields=["plate_no", "brand", "model", "year", "value"],
        next_stage_success=ConversationStage.ASK_ANOTHER_VEHICLE
    ),
    ConversationStage.ASK_ANOTHER_VEHICLE: StageHandler(
        stage=ConversationStage.ASK_ANOTHER_VEHICLE,
        prompt_template="ask_another_vehicle",
        expected_input="choice_number",
        next_stage_success=ConversationStage.FETCHING_OFFERS
    ),
    ConversationStage.SHOWING_OFFERS: StageHandler(
        stage=ConversationStage.SHOWING_OFFERS,
        prompt_template="showing_offers",
        next_stage_success=ConversationStage.AWAITING_SELECTION
    ),
    ConversationStage.AWAITING_SELECTION: StageHandler(
        stage=ConversationStage.AWAITING_SELECTION,
        prompt_template="awaiting_selection",
        expected_input="choice_number",
        next_stage_success=ConversationStage.CONFIRMATION
    ),
    ConversationStage.CONFIRMATION: StageHandler(
        stage=ConversationStage.CONFIRMATION,
        prompt_template="confirmation",
        expected_input="choice_number",
        next_stage_success=ConversationStage.CREATING_INVOICE
    ),
    ConversationStage.PENDING_PAYMENT: StageHandler(
        stage=ConversationStage.PENDING_PAYMENT,
        prompt_template="pending_payment",
        expected_input="payment_confirm",
        next_stage_success=ConversationStage.ISSUING_POLICY
    ),
}
