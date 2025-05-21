"""
Utility functions for AI integration with OpenAI models.
"""
import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
import requests
from django.conf import settings
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# OpenAI API endpoints
OPENAI_API_URL = "https://api.openai.com/v1"
CHAT_COMPLETIONS_ENDPOINT = f"{OPENAI_API_URL}/chat/completions"

class AIModelContext:
    """Base class for AI model contexts."""
    
    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def generate_response(self, messages: List[Dict[str, str]], 
                          temperature: float = 0.7, 
                          max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate a response from the AI model.
        
        Args:
            messages: List of message objects with role and content
            temperature: Controls randomness (0-1)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Response from the API as a dictionary
        """
        try:
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(
                CHAT_COMPLETIONS_ENDPOINT,
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}", "details": response.text}
                
        except Exception as e:
            logger.exception(f"Error generating AI response: {str(e)}")
            return {"error": f"Failed to generate response: {str(e)}"}
    
    def extract_content(self, response: Dict[str, Any]) -> str:
        """Extract the content from the API response."""
        try:
            if "error" in response:
                return f"Error: {response['error']}"
            
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting content from response: {str(e)}")
            return "Error extracting content from response"


class GPT4Context(AIModelContext):
    """Context for GPT-4 model."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "gpt-4o")


class GPT1Context(AIModelContext):
    """Context for GPT-1 model (using GPT-3.5-turbo as a substitute since GPT-1 is not available via API)."""
    
    def __init__(self, api_key: str):
        super().__init__(api_key, "gpt-3.5-turbo")


def get_user_ai_context(user: User, model_type: str = "gpt4") -> Optional[AIModelContext]:
    """
    Get the AI context for a user based on their API key.
    
    Args:
        user: The user to get the AI context for
        model_type: The type of model to use (gpt4 or gpt1)
        
    Returns:
        An AIModelContext object or None if the user doesn't have an API key
    """
    try:
        if not hasattr(user, 'profile') or not user.profile.chatgpt_api_key:
            return None
        
        api_key = user.profile.chatgpt_api_key
        
        if model_type.lower() == "gpt4":
            return GPT4Context(api_key)
        elif model_type.lower() == "gpt1":
            return GPT1Context(api_key)
        else:
            logger.error(f"Unknown model type: {model_type}")
            return None
            
    except Exception as e:
        logger.exception(f"Error getting AI context for user {user.username}: {str(e)}")
        return None


def generate_vibe_content(user: User, vibe_title: str, vibe_description: str) -> Dict[str, Any]:
    """
    Generate content for a vibe using OpenAI.
    
    Args:
        user: The user who owns the vibe
        vibe_title: The title of the vibe
        vibe_description: The description of the vibe
        
    Returns:
        A dictionary with generated content or error message
    """
    context = get_user_ai_context(user)
    if not context:
        return {"error": "No OpenAI API key found for this user"}
    
    messages = [
        {"role": "system", "content": "You are a creative assistant that helps generate content for a vibe page. A vibe is a personalized digital space that reflects a specific mood, theme, or aesthetic."},
        {"role": "user", "content": f"Generate content for my vibe titled '{vibe_title}'. Description: {vibe_description}. Please provide: 1) A short tagline, 2) Three key elements that define this vibe, 3) A color palette suggestion (with hex codes), and 4) A short paragraph expanding on the vibe's essence."}
    ]
    
    response = context.generate_response(messages)
    content = context.extract_content(response)
    
    return {
        "success": "error" not in response,
        "content": content,
        "raw_response": response
    }
