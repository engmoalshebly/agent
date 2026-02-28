"""
Decision Applier - Applies LLM decisions to conversation context
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from app.engine.session_manager import ConversationContext
from app.core.constants import ConversationStage
from app.engine.vehicle_manager import VehicleManager

logger = logging.getLogger(__name__)


class DecisionApplier:
    """Applies LLM decisions to conversation context with validation"""
    
    async def apply_decision(
        self,
        context: ConversationContext,
        llm_decision,  # LLMDecision type
        user_message: str
    ) -> ConversationContext:
        """
        Apply LLM decision to context with proper validation and state management
        """
        
        logger.info(f"🔄 Applying decision: {llm_decision.stage} with actions: {llm_decision.actions}")
        
        # 1. Apply extracted data to context
        await self._apply_extracted_data(context, llm_decision.extracted)
        
        # 2. Apply stage transition
        await self._apply_stage_transition(context, llm_decision.stage)
        
        # 3. Update conversation metadata
        context.last_question = llm_decision.last_question
        context.updated_at = datetime.now()
        
        # 4. Apply specific actions
        await self._apply_actions(context, llm_decision.actions, user_message)
        
        # 5. Validate context integrity
        await self._validate_context_integrity(context)
        
        return context
    
    async def _apply_extracted_data(
        self, 
        context: ConversationContext, 
        extracted: Dict[str, Any]
    ):
        """Apply extracted data to appropriate context fields"""
        
        if not extracted:
            return
        
        # Ensure data dictionaries exist
        context.profile_data = context.profile_data or {}
        context.vehicle_data = context.vehicle_data or {}
        
        for field, value in extracted.items():
            if field in ["national_id", "birth_date", "phone"]:
                # Profile data
                context.profile_data[field] = value
                logger.info(f"✅ Updated profile: {field}")
            
            elif field in ["plate_number", "brand", "model", "year", "vehicle_value", "registration_type"]:
                # Vehicle data - handle through VehicleManager
                await self._update_vehicle_data(context, field, value)
            
            elif field == "choice":
                # Handle user choices
                context.last_choice = value
                logger.info(f"✅ Recorded choice: {value}")
            
            else:
                # Store in general data
                if "extracted_data" not in context.profile_data:
                    context.profile_data["extracted_data"] = {}
                context.profile_data["extracted_data"][field] = value
                logger.info(f"✅ Stored extracted data: {field}")
    
    async def _update_vehicle_data(
        self, 
        context: ConversationContext, 
        field: str, 
        value: Any
    ):
        """Update vehicle data through VehicleManager"""
        
        try:
            # Get or create VehicleManager
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
            else:
                vm = VehicleManager(context.conversation_id)
                vm.start_new_vehicle()
            
            # Ensure there's a current vehicle
            if not vm.vehicles:
                vm.start_new_vehicle()
            
            # Update current vehicle
            if field == "plate_number":
                vm.update_current(plate_no=value)
            elif field == "brand":
                vm.update_current(brand=value)
            elif field == "model":
                vm.update_current(model=value)
            elif field == "year":
                vm.update_current(year=int(value) if isinstance(value, str) and value.isdigit() else value)
            elif field == "vehicle_value":
                vm.update_current(value=value)
            elif field == "registration_type":
                vm.update_current(registration_type=value)
            
            # Save back to context
            context.vehicle_data["manager"] = vm.to_dict()
            logger.info(f"✅ Updated vehicle: {field} = {value}")
            
        except Exception as e:
            logger.error(f"❌ Error updating vehicle data: {e}")
    
    async def _apply_stage_transition(
        self, 
        context: ConversationContext, 
        new_stage: str
    ):
        """Apply stage transition with validation"""
        
        try:
            # Convert string to ConversationStage enum
            if isinstance(new_stage, str):
                new_stage_enum = ConversationStage(new_stage)
            else:
                new_stage_enum = new_stage
            
            # Validate transition
            if self._is_valid_transition(context.current_stage, new_stage_enum):
                old_stage = context.current_stage
                context.current_stage = new_stage_enum
                logger.info(f"✅ Stage transition: {old_stage.value} → {new_stage_enum.value}")
            else:
                logger.warning(f"⚠️ Invalid stage transition: {context.current_stage.value} → {new_stage}")
        
        except ValueError as e:
            logger.error(f"❌ Invalid stage value: {new_stage}")
    
    def _is_valid_transition(
        self, 
        current_stage: ConversationStage, 
        new_stage: ConversationStage
    ) -> bool:
        """Validate if stage transition is allowed"""
        
        # Allow staying in same stage
        if current_stage == new_stage:
            return True
        
        # Define valid transitions
        valid_transitions = {
            ConversationStage.GREETING: [
                ConversationStage.COLLECTING_PROFILE,
                ConversationStage.HELP
            ],
            ConversationStage.COLLECTING_PROFILE: [
                ConversationStage.COLLECTING_VEHICLE,
                ConversationStage.GREETING,  # Allow going back
                ConversationStage.HELP
            ],
            ConversationStage.COLLECTING_VEHICLE: [
                ConversationStage.ASK_ANOTHER_VEHICLE,
                ConversationStage.COLLECTING_PROFILE,  # Allow going back
                ConversationStage.HELP
            ],
            ConversationStage.ASK_ANOTHER_VEHICLE: [
                ConversationStage.COLLECTING_VEHICLE,  # Add another vehicle
                ConversationStage.SHOWING_OFFERS,      # Show offers
                ConversationStage.HELP
            ],
            ConversationStage.SHOWING_OFFERS: [
                ConversationStage.AWAITING_SELECTION,
                ConversationStage.COLLECTING_VEHICLE,  # Allow going back
                ConversationStage.HELP
            ],
            ConversationStage.AWAITING_SELECTION: [
                ConversationStage.CONFIRMATION,
                ConversationStage.SHOWING_OFFERS,  # Allow going back
                ConversationStage.HELP
            ],
            ConversationStage.CONFIRMATION: [
                ConversationStage.PENDING_PAYMENT,
                ConversationStage.COLLECTING_PROFILE,  # Start over
                ConversationStage.GREETING,            # Start fresh
                ConversationStage.HELP
            ],
            ConversationStage.PENDING_PAYMENT: [
                ConversationStage.ISSUING_POLICY,
                ConversationStage.CONFIRMATION,  # Allow going back
                ConversationStage.HELP
            ],
            ConversationStage.ISSUING_POLICY: [
                ConversationStage.DONE,
                ConversationStage.HELP
            ],
            ConversationStage.DONE: [
                ConversationStage.GREETING,  # New conversation
                ConversationStage.HELP
            ],
            ConversationStage.HELP: [
                # Help can go to any stage
                ConversationStage.GREETING,
                ConversationStage.COLLECTING_PROFILE,
                ConversationStage.COLLECTING_VEHICLE,
                ConversationStage.ASK_ANOTHER_VEHICLE,
                ConversationStage.SHOWING_OFFERS,
                ConversationStage.AWAITING_SELECTION,
                ConversationStage.CONFIRMATION,
                ConversationStage.PENDING_PAYMENT,
                ConversationStage.ISSUING_POLICY,
                ConversationStage.DONE
            ]
        }
        
        allowed_stages = valid_transitions.get(current_stage, [])
        return new_stage in allowed_stages
    
    async def _apply_actions(
        self, 
        context: ConversationContext, 
        actions: list, 
        user_message: str
    ):
        """Apply specific actions from LLM decision"""
        
        for action in actions:
            try:
                if action == "create_offers":
                    await self._create_offers(context)
                
                elif action == "create_invoice":
                    await self._create_invoice(context)
                
                elif action == "add_vehicle":
                    await self._add_new_vehicle(context)
                
                elif action == "validate_profile":
                    await self._validate_profile_completeness(context)
                
                elif action == "validate_vehicle":
                    await self._validate_vehicle_completeness(context)
                
                elif action.startswith("select_offer_"):
                    offer_id = int(action.split("_")[-1])
                    await self._select_offer(context, offer_id)
                
                else:
                    logger.info(f"ℹ️ Unknown action: {action}")
            
            except Exception as e:
                logger.error(f"❌ Error applying action {action}: {e}")
    
    async def _create_offers(self, context: ConversationContext):
        """Create insurance offers based on vehicle data"""
        
        # Mock offers - in production, this would call external service
        offers = [
            {"id": 1, "type": "شامل", "price": 2850, "company": "شركة التأمين الأولى"},
            {"id": 2, "type": "شامل+", "price": 3200, "company": "شركة التأمين الثانية"},
            {"id": 3, "type": "ضد الغير", "price": 1100, "company": "شركة التأمين الثالثة"},
            {"id": 4, "type": "ضد الغير+", "price": 1450, "company": "شركة التأمين الرابعة"},
        ]
        
        context.offers_shown = offers
        logger.info(f"✅ Created {len(offers)} insurance offers")
    
    async def _create_invoice(self, context: ConversationContext):
        """Create invoice for selected offer"""
        
        if context.selected_offer:
            import random
            context.order_id = random.randint(10000, 99999)
            context.invoice_id = random.randint(1000, 9999)
            logger.info(f"✅ Created invoice: {context.invoice_id} for order: {context.order_id}")
    
    async def _add_new_vehicle(self, context: ConversationContext):
        """Add new vehicle to VehicleManager"""
        
        try:
            manager_data = context.vehicle_data.get("manager", {})
            if manager_data:
                vm = VehicleManager.from_dict(manager_data)
            else:
                vm = VehicleManager(context.conversation_id)
            
            vm.start_new_vehicle()
            context.vehicle_data["manager"] = vm.to_dict()
            logger.info("✅ Added new vehicle slot")
        
        except Exception as e:
            logger.error(f"❌ Error adding new vehicle: {e}")
    
    async def _select_offer(self, context: ConversationContext, offer_id: int):
        """Select specific offer"""
        
        if context.offers_shown and 1 <= offer_id <= len(context.offers_shown):
            context.selected_offer = context.offers_shown[offer_id - 1]
            context.selected_offer_id = offer_id
            logger.info(f"✅ Selected offer {offer_id}: {context.selected_offer['type']}")
    
    async def _validate_profile_completeness(self, context: ConversationContext):
        """Validate if profile data is complete"""
        
        required_fields = ["national_id", "birth_date"]
        profile_data = context.profile_data or {}
        
        missing_fields = [field for field in required_fields if field not in profile_data]
        
        if missing_fields:
            logger.info(f"⚠️ Profile incomplete, missing: {missing_fields}")
            context.profile_complete = False
        else:
            logger.info("✅ Profile data complete")
            context.profile_complete = True
    
    async def _validate_vehicle_completeness(self, context: ConversationContext):
        """Validate if vehicle data is complete"""
        
        manager_data = context.vehicle_data.get("manager", {})
        if not manager_data:
            context.vehicle_complete = False
            return
        
        vehicles = manager_data.get("vehicles", [])
        if not vehicles:
            context.vehicle_complete = False
            return
        
        # Check if at least one vehicle is complete
        for vehicle in vehicles:
            required_fields = ["plate_no", "brand", "value"]
            if all(field in vehicle and vehicle[field] for field in required_fields):
                context.vehicle_complete = True
                logger.info("✅ At least one vehicle is complete")
                return
        
        context.vehicle_complete = False
        logger.info("⚠️ No complete vehicles found")
    
    async def _validate_context_integrity(self, context: ConversationContext):
        """Final validation of context integrity"""
        
        # Ensure required fields exist
        context.profile_data = context.profile_data or {}
        context.vehicle_data = context.vehicle_data or {}
        
        # Validate stage-specific requirements
        if context.current_stage == ConversationStage.COLLECTING_VEHICLE:
            if "manager" not in context.vehicle_data:
                # Initialize VehicleManager if missing
                vm = VehicleManager(context.conversation_id)
                vm.start_new_vehicle()
                context.vehicle_data["manager"] = vm.to_dict()
                logger.info("✅ Initialized missing VehicleManager")
        
        # Update timestamps
        context.updated_at = datetime.now()
        
        logger.info(f"✅ Context integrity validated for stage: {context.current_stage.value}")