"""
Base classes for AI model integration with OpenAI models.
"""
import logging
import requests
import json
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# OpenAI API endpoints
OPENAI_API_URL = "https://api.openai.com/v1"
CHAT_COMPLETIONS_ENDPOINT = f"{OPENAI_API_URL}/chat/completions"

# Define the available tools for the AI
VIBE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the content of a file in the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to read"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or update a file in the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to write"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write to the file"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file from the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "The name of the file to delete"
                    }
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_image",
            "description": "Generate an image using DALL-E and save it to the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The prompt to generate an image from"
                    },
                    "size": {
                        "type": "string",
                        "description": "The size of the image (1024x1024, 1024x1792, or 1792x1024)",
                        "enum": ["1024x1024", "1024x1792", "1792x1024"]
                    },
                    "quality": {
                        "type": "string",
                        "description": "The quality of the image (standard or hd)",
                        "enum": ["standard", "hd"]
                    },
                    "filename": {
                        "type": "string",
                        "description": "The name to save the image as (optional)"
                    }
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_image",
            "description": "Save an image from a URL to the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the image to save"
                    },
                    "filename": {
                        "type": "string",
                        "description": "The name to save the image as (optional)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_images",
            "description": "List all images available to the user and in the vibe directory",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "explain_image_workflow",
            "description": "Get a detailed explanation of how to generate and use images properly",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

class AIModelContext:
    """Base class for AI model contexts."""

    def __init__(self, api_key: str, model: str):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        self.tools = VIBE_TOOLS

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
            # Configure the payload with O1 reasoning parameters
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "tools": self.tools,
                "tool_choice": "auto"
            }

            logger.debug(f"Sending request to OpenAI API with payload: {json.dumps(payload)[:500]}...")

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

            message = response["choices"][0]["message"]
            content = message.get("content", "")

            # Check if there are tool calls in the response
            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                # Format tool calls in the content for backward compatibility
                for tool_call in tool_calls:
                    function = tool_call.get("function", {})
                    name = function.get("name", "")
                    arguments = function.get("arguments", "{}")

                    try:
                        args = json.loads(arguments)

                        # Format the tool call based on the function name
                        if name == "list_files":
                            tool_content = f"list_files"
                        elif name == "read_file":
                            tool_content = f"read_file\nfilename: {args.get('filename', '')}"
                        elif name == "write_file":
                            tool_content = f"write_file\nfilename: {args.get('filename', '')}\ncontent:\n{args.get('content', '')}"
                        elif name == "delete_file":
                            tool_content = f"delete_file\nfilename: {args.get('filename', '')}"
                        elif name == "generate_image":
                            tool_content = f"generate_image\nprompt: {args.get('prompt', '')}"
                            if "size" in args:
                                tool_content += f"\nsize: {args.get('size')}"
                            if "quality" in args:
                                tool_content += f"\nquality: {args.get('quality')}"
                            if "filename" in args:
                                tool_content += f"\nfilename: {args.get('filename')}"
                        elif name == "save_image":
                            tool_content = f"save_image\nurl: {args.get('url', '')}"
                            if "filename" in args:
                                tool_content += f"\nfilename: {args.get('filename')}"
                        elif name == "list_images":
                            tool_content = f"list_images"
                        elif name == "explain_image_workflow":
                            tool_content = f"explain_image_workflow"
                        else:
                            tool_content = f"{name}\n{arguments}"

                        # Add the formatted tool call to the content
                        if content:
                            content += f"\n\n```tool\n{tool_content}\n```\n\n"
                        else:
                            content = f"```tool\n{tool_content}\n```\n\n"

                    except json.JSONDecodeError:
                        logger.error(f"Error parsing tool call arguments: {arguments}")
                        content += f"\n\nError parsing tool call: {name}\n\n"

            return content
        except (KeyError, IndexError) as e:
            logger.error(f"Error extracting content from response: {str(e)}")
            return "Error extracting content from response"


class GPT4Context(AIModelContext):
    """Context for GPT-4 model."""

    def __init__(self, api_key: str):
        super().__init__(api_key, "gpt-4o-2024-05-13")


class GPT1Context(AIModelContext):
    """Context for GPT-1 model (using GPT-3.5-turbo as a substitute since GPT-1 is not available via API)."""

    def __init__(self, api_key: str):
        super().__init__(api_key, "gpt-3.5-turbo-0125")


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
