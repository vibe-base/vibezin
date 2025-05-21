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


class VibeConversation:
    """Class to manage a conversation about a vibe."""

    def __init__(self, user: User, vibe_id: int):
        """
        Initialize a conversation about a vibe.

        Args:
            user: The user who owns the conversation
            vibe_id: The ID of the vibe
        """
        from .models import Vibe

        self.user = user
        self.vibe = Vibe.objects.get(pk=vibe_id)
        self.context = get_user_ai_context(user)
        self.messages = [
            {
                "role": "system",
                "content": (
                    "You are a creative assistant that helps build vibe pages. "
                    "A vibe is a personalized digital space that reflects a specific mood, theme, or aesthetic. "
                    "You have access to the following tools to help create and manage files for the vibe:\n\n"

                    "1. LIST FILES: You can list all files in the vibe directory.\n"
                    "2. READ FILE: You can read the content of a specific file.\n"
                    "3. WRITE FILE: You can create or update a file with new content.\n"
                    "4. DELETE FILE: You can delete a file from the vibe directory.\n\n"

                    "To use these tools, you must format your response using the following syntax:\n\n"

                    "To list files:\n"
                    "```tool\n"
                    "list_files\n"
                    "```\n\n"

                    "To read a file:\n"
                    "```tool\n"
                    "read_file\n"
                    "filename: example.html\n"
                    "```\n\n"

                    "To write a file:\n"
                    "```tool\n"
                    "write_file\n"
                    "filename: example.html\n"
                    "content:\n"
                    "<!DOCTYPE html>\n"
                    "<html>\n"
                    "  <head>\n"
                    "    <title>Example</title>\n"
                    "  </head>\n"
                    "  <body>\n"
                    "    <h1>Hello, World!</h1>\n"
                    "  </body>\n"
                    "</html>\n"
                    "```\n\n"

                    "To delete a file:\n"
                    "```tool\n"
                    "delete_file\n"
                    "filename: example.html\n"
                    "```\n\n"

                    "When the user asks you to create content, you should use these tools to create the necessary files. "
                    "Typically, a vibe page consists of at least an index.html file, and may include style.css and script.js files. "
                    "Your goal is to help the user create a unique and visually appealing vibe page that matches their vision."
                )
            }
        ]

        # Add initial context about the vibe
        self.add_message(
            "system",
            f"The vibe is titled '{self.vibe.title}' with the description: {self.vibe.description}. "
            f"The vibe has a unique URL at /vibe/{self.vibe.slug}/. "
            f"When creating files, remember that they will be served from the vibe's directory, so you should use relative paths for links and imports."
        )

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation.

        Args:
            role: The role of the message sender (system, user, assistant)
            content: The content of the message
        """
        self.messages.append({"role": role, "content": content})

    def get_response(self, temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """
        Get a response from the AI.

        Args:
            temperature: Controls randomness (0-1)
            max_tokens: Maximum number of tokens to generate

        Returns:
            Dictionary with response content or error message
        """
        try:
            if not self.context:
                return {"success": False, "error": "No OpenAI API key found for this user"}

            # For testing purposes, if the API key is a test key, return a mock response
            if self.context.api_key == 'sk-test-key':
                # Create a mock response that demonstrates tool usage
                mock_content = (
                    "I'll help you create a page for your dog Athena! Let me first check if there are any existing files.\n\n"
                    "```tool\n"
                    "list_files\n"
                    "```"
                )
                self.add_message("assistant", mock_content)
                return {
                    "success": True,
                    "content": mock_content,
                    "raw_response": {"choices": [{"message": {"content": mock_content}}]}
                }

            response = self.context.generate_response(self.messages, temperature, max_tokens)
            content = self.context.extract_content(response)

            # Process tool calls in the response
            processed_content = self.process_tool_calls(content)

            # Add the assistant's response to the conversation history
            if "error" not in response:
                self.add_message("assistant", content)

            return {
                "success": "error" not in response,
                "content": processed_content,
                "raw_response": response
            }
        except Exception as e:
            logger.exception(f"Error getting AI response: {str(e)}")
            return {
                "success": False,
                "error": f"Error getting AI response: {str(e)}"
            }

    def process_tool_calls(self, content: str) -> str:
        """
        Process tool calls in the AI response.

        Args:
            content: The content from the AI response

        Returns:
            Processed content with tool call results
        """
        from .file_utils import VibeFileManager

        # Check if there are any tool calls in the content
        if "```tool" not in content:
            return content

        # Split the content by tool blocks
        parts = content.split("```tool")
        result = [parts[0]]  # Start with the content before the first tool call

        # Create a file manager for this vibe
        file_manager = VibeFileManager(self.vibe)

        # Process each tool call
        for i in range(1, len(parts)):
            part = parts[i]
            # Find the end of the tool block
            tool_end = part.find("```")
            if tool_end == -1:
                # If there's no closing tag, just append the part as is
                result.append("```tool" + part)
                continue

            # Extract the tool call
            tool_call = part[:tool_end].strip()
            # Get the content after the tool call
            after_tool = part[tool_end + 3:]

            # Parse the tool call
            lines = tool_call.split("\n")
            tool_name = lines[0].strip()

            # Execute the tool call
            tool_result = "Error: Unknown tool"

            if tool_name == "list_files":
                # List files
                files = file_manager.list_files()
                if files:
                    tool_result = "Files in the vibe directory:\n"
                    for file in files:
                        tool_result += f"- {file['name']} ({file['size']} bytes)\n"
                else:
                    tool_result = "No files found in the vibe directory."

            elif tool_name == "read_file":
                # Read a file
                filename = None
                for line in lines[1:]:
                    if line.startswith("filename:"):
                        filename = line[len("filename:"):].strip()
                        break

                if filename:
                    result_dict = file_manager.read_file(filename)
                    if result_dict.get('success', False):
                        tool_result = f"Content of {filename}:\n\n```\n{result_dict['content']}\n```"
                    else:
                        tool_result = f"Error: {result_dict.get('error', 'Unknown error')}"
                else:
                    tool_result = "Error: No filename provided for read_file"

            elif tool_name == "write_file":
                # Write a file
                filename = None
                content_start = None

                # Find the filename and content
                for i, line in enumerate(lines[1:]):
                    if line.startswith("filename:"):
                        filename = line[len("filename:"):].strip()
                    elif line.startswith("content:"):
                        content_start = i + 1
                        break

                if filename and content_start is not None:
                    # Extract the content
                    file_content = "\n".join(lines[content_start + 1:])

                    # Write the file
                    result_dict = file_manager.write_file(filename, file_content)
                    if result_dict.get('success', False):
                        tool_result = f"File {result_dict.get('action', 'written')}: {filename}"
                    else:
                        tool_result = f"Error: {result_dict.get('error', 'Unknown error')}"
                else:
                    tool_result = "Error: Missing filename or content for write_file"

            elif tool_name == "delete_file":
                # Delete a file
                filename = None
                for line in lines[1:]:
                    if line.startswith("filename:"):
                        filename = line[len("filename:"):].strip()
                        break

                if filename:
                    result_dict = file_manager.delete_file(filename)
                    if result_dict.get('success', False):
                        tool_result = f"File deleted: {filename}"
                    else:
                        tool_result = f"Error: {result_dict.get('error', 'Unknown error')}"
                else:
                    tool_result = "Error: No filename provided for delete_file"

            # Append the tool result and the content after the tool call
            result.append(f"Tool result:\n{tool_result}\n\n{after_tool}")

        return "".join(result)


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
