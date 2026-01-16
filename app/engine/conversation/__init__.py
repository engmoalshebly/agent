"""
Conversation Module - إدارة المحادثات
"""
from .history import (
    ConversationMessage,
    ConversationHistory,
    get_or_create_history,
    clear_history,
    get_all_conversation_ids,
)
from .prompts import (
    SYSTEM_PROMPT,
    STAGE_INFO_MAP,
    get_stage_info,
    get_data_summary,
    get_missing_data,
    get_stage_specific_instruction,
    format_services,
)

__all__ = [
    # History
    "ConversationMessage",
    "ConversationHistory",
    "get_or_create_history",
    "clear_history",
    "get_all_conversation_ids",
    # Prompts
    "SYSTEM_PROMPT",
    "STAGE_INFO_MAP",
    "get_stage_info",
    "get_data_summary",
    "get_missing_data",
    "get_stage_specific_instruction",
    "format_services",
]
