"""
AI module for Vibezin.
"""

# Re-export classes and functions from submodules
from ..ai_models import (
    AIModelContext,
    GPT4Context,
    GPT1Context,
    get_user_ai_context
)

from ..ai_conversation import (
    VibeConversation,
    generate_vibe_content
)

from ..ai_tools import (
    process_tool_calls,
    handle_list_files,
    handle_read_file,
    handle_write_file,
    handle_delete_file,
    handle_generate_image,
    handle_save_image
)

from ..ai_image_generation import (
    generate_image,
    save_generated_image
)

from ..ai_prompts import (
    VIBE_BUILDER_SYSTEM_PROMPT,
    get_vibe_context_prompt,
    CONTENT_GENERATION_PROMPT
)

from ..ai_mock_responses import (
    get_mock_response
)

# For backward compatibility
__all__ = [
    # AI Models
    'AIModelContext',
    'GPT4Context',
    'GPT1Context',
    'get_user_ai_context',
    
    # AI Conversation
    'VibeConversation',
    'generate_vibe_content',
    
    # AI Tools
    'process_tool_calls',
    'handle_list_files',
    'handle_read_file',
    'handle_write_file',
    'handle_delete_file',
    'handle_generate_image',
    'handle_save_image',
    
    # AI Image Generation
    'generate_image',
    'save_generated_image',
    
    # AI Prompts
    'VIBE_BUILDER_SYSTEM_PROMPT',
    'get_vibe_context_prompt',
    'CONTENT_GENERATION_PROMPT',
    
    # AI Mock Responses
    'get_mock_response'
]
