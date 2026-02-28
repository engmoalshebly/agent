"""
Transitions module - Stage transition management
"""
from app.engine.transitions.stage_transitions import StageTransitionManager

# Create global instance
stage_transition_manager = StageTransitionManager()

__all__ = ['stage_transition_manager', 'StageTransitionManager']