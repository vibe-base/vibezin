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
        """
        Extract the content from the API response, handling both regular content and tool calls.

        This method processes the response from the OpenAI API, extracting both the text content
        and any tool calls. Tool calls are formatted as code blocks with the 'tool' language
        for backward compatibility with the existing tool processing system.

        Args:
            response: The raw response from the OpenAI API

        Returns:
            A string containing the formatted content and tool calls
        """
        try:
            if "error" in response:
                logger.error(f"Error in API response: {response['error']}")
                return f"Error: {response['error']}"

            # Get the message from the response
            message = response["choices"][0]["message"]

            # Get the content (might be empty if only tool calls are present)
            content = message.get("content", "")

            # Log the raw content for debugging
            logger.debug(f"Raw content from API: {content[:100]}...")

            # We're no longer using JSON response format with tool calls
            # But keep this code in case the content is still in JSON format for some reason
            if content and content.strip().startswith("{") and content.strip().endswith("}"):
                try:
                    # Try to parse the content as JSON
                    content_json = json.loads(content)
                    logger.info("Content appears to be in JSON format, attempting to extract")

                    # Extract the actual content from the JSON
                    if "content" in content_json:
                        content = content_json["content"]
                        logger.info("Extracted content from JSON 'content' field")
                    elif "response" in content_json:
                        content = content_json["response"]
                        logger.info("Extracted content from JSON 'response' field")
                    elif "message" in content_json:
                        content = content_json["message"]
                        logger.info("Extracted content from JSON 'message' field")
                    elif "text" in content_json:
                        content = content_json["text"]
                        logger.info("Extracted content from JSON 'text' field")
                    else:
                        # If we can't find a specific field, just stringify the JSON
                        logger.info("No specific content field found in JSON, using full JSON")
                        content = json.dumps(content_json, indent=2)

                    logger.debug(f"Extracted content from JSON: {content[:100]}...")
                except json.JSONDecodeError:
                    # Not valid JSON, keep the original content
                    logger.debug("Content appears to be JSON-like but is not valid JSON, keeping as is")
                    pass

            # Check if there are tool calls in the response
            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                logger.info(f"Found {len(tool_calls)} tool calls in the response")

                # Format tool calls in the content for backward compatibility
                for i, tool_call in enumerate(tool_calls):
                    function = tool_call.get("function", {})
                    name = function.get("name", "")
                    arguments = function.get("arguments", "{}")

                    logger.info(f"Processing tool call {i+1}: {name}")
                    logger.debug(f"Tool call arguments: {arguments}")

                    try:
                        args = json.loads(arguments)

                        # Format the tool call based on the function name
                        if name == "list_files":
                            tool_content = f"list_files"
                        elif name == "read_file":
                            tool_content = f"read_file\nfilename: {args.get('filename', '')}"
                        elif name == "write_file":
                            # For write_file, make sure to properly format the content
                            filename = args.get('filename', '')
                            file_content = args.get('content', '')
                            tool_content = f"write_file\nfilename: {filename}\ncontent:\n{file_content}"

                            # Log the write_file operation for debugging
                            logger.info(f"write_file tool call: filename={filename}, content_length={len(file_content)}")
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
    """Context for GPT-4 model with O1 reasoning capabilities."""

    def __init__(self, api_key: str):
        # Use gpt-4o which supports the O1 reasoning engine
        super().__init__(api_key, "gpt-4o")

    def generate_response(self, messages: List[Dict[str, str]],
                          temperature: float = 0.7,
                          max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Generate a response from the AI model with O1 reasoning enabled.

        This overrides the base class method to add specific parameters for O1 reasoning.

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
                # IMPORTANT: Do NOT use response_format with tool calls
                # It causes conflicts with the tool call format
            }

            logger.info(f"Sending request to OpenAI API with O1 reasoning enabled")
            logger.debug(f"Payload: {json.dumps(payload)[:500]}...")

            response = requests.post(
                CHAT_COMPLETIONS_ENDPOINT,
                headers=self.headers,
                json=payload
            )

            if response.status_code == 200:
                logger.info("Successfully received response from OpenAI API")
                return response.json()
            else:
                logger.error(f"API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code}", "details": response.text}

        except Exception as e:
            logger.exception(f"Error generating AI response: {str(e)}")
            return {"error": f"Failed to generate response: {str(e)}"}


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
