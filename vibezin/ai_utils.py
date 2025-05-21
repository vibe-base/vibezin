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
                    "You are a creative assistant that helps build vibe pages using the O1 reasoning engine. "
                    "A vibe is a personalized digital space that reflects a specific mood, theme, or aesthetic. "
                    "You MUST use the available tools to create and save actual files in response to user requests. "
                    "DO NOT just respond with HTML code in the conversation - you must save the files using the tools.\n\n"

                    "IMPORTANT: When a user asks you to create a page or content, you MUST:\n"
                    "1. Use the O1 reasoning engine to plan what files you need to create (typically index.html, style.css, script.js)\n"
                    "2. Check if any files already exist using the list_files tool\n"
                    "3. Create or update the necessary files using the write_file tool\n"
                    "4. Confirm to the user that you've created the files\n\n"

                    "You have access to the following tools:\n\n"

                    "1. LIST FILES: You can list all files in the vibe directory.\n"
                    "2. READ FILE: You can read the content of a specific file.\n"
                    "3. WRITE FILE: You can create or update a file with new content.\n"
                    "4. DELETE FILE: You can delete a file from the vibe directory.\n"
                    "5. GENERATE IMAGE: You can generate an image using DALL-E and insert it into your HTML.\n"
                    "6. SAVE IMAGE: You can save an image from a URL directly to the vibe directory.\n\n"

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
                    "filename: index.html\n"
                    "content:\n"
                    "<!DOCTYPE html>\n"
                    "<html>\n"
                    "  <head>\n"
                    "    <title>Example</title>\n"
                    "    <link rel=\"stylesheet\" href=\"style.css\">\n"
                    "  </head>\n"
                    "  <body>\n"
                    "    <h1>Hello, World!</h1>\n"
                    "    <script src=\"script.js\"></script>\n"
                    "  </body>\n"
                    "</html>\n"
                    "```\n\n"

                    "To delete a file:\n"
                    "```tool\n"
                    "delete_file\n"
                    "filename: example.html\n"
                    "```\n\n"

                    "To generate an image with DALL-E:\n"
                    "```tool\n"
                    "generate_image\n"
                    "prompt: A beautiful sunset over a mountain landscape\n"
                    "size: 1024x1024\n"
                    "```\n\n"

                    "To save an image from a URL to the vibe directory:\n"
                    "```tool\n"
                    "save_image\n"
                    "url: https://example.com/image.jpg\n"
                    "filename: my_image.jpg\n"
                    "```\n\n"

                    "EXAMPLE WORKFLOW:\n"
                    "1. User asks: \"Create a page about my dog Max\"\n"
                    "2. You should first list files: ```tool\nlist_files\n```\n"
                    "3. If the user wants images, you can either:\n"
                    "   a. Generate a new image: ```tool\ngenerate_image\nprompt: A cute dog named Max\nsize: 1024x1024\nfilename: max_dog.png\n```\n"
                    "   b. Or save an existing image: ```tool\nsave_image\nurl: https://example.com/dog.jpg\nfilename: max.jpg\n```\n"
                    "4. Then create an index.html file that includes the image: ```tool\nwrite_file\nfilename: index.html\ncontent:\n<!DOCTYPE html>...<img src=\"/static/vibes/vibe-slug/max_dog.png\" alt=\"A cute dog named Max\">...\n```\n"
                    "5. Then create a style.css file: ```tool\nwrite_file\nfilename: style.css\ncontent:\n...\n```\n"
                    "6. Then create a script.js file if needed: ```tool\nwrite_file\nfilename: script.js\ncontent:\n...\n```\n"
                    "7. Finally, confirm to the user that you've created the files\n\n"
                    "IMPORTANT: When generating images with DALL-E, the images will be saved directly to the vibe's folder. You should use the local path returned by the tool to reference the image in your HTML files. DO NOT show the image in the conversation - it's already saved to the vibe folder.\n\n"

                    "Remember, you MUST use the tools to create actual files. DO NOT just respond with HTML code in the conversation."
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
                # Create a mock response that demonstrates proper tool usage with O1 reasoning
                mock_content = (
                    "I'll help you create a page for your dog Athena! I'll use the O1 reasoning engine to plan and create the necessary files.\n\n"
                    "First, let me check if there are any existing files in your vibe directory:\n\n"
                    "```tool\n"
                    "list_files\n"
                    "```\n\n"
                    "Let me generate an image of a cute dog for Athena's page:\n\n"
                    "```tool\n"
                    "generate_image\n"
                    "prompt: A cute golden retriever dog named Athena, photorealistic\n"
                    "size: 1024x1024\n"
                    "filename: athena_dog.png\n"
                    "```\n\n"
                    "Now I'll create an index.html file for Athena's page that includes the image:\n\n"
                    "```tool\n"
                    "write_file\n"
                    "filename: index.html\n"
                    "content:\n"
                    "<!DOCTYPE html>\n"
                    "<html lang=\"en\">\n"
                    "<head>\n"
                    "    <meta charset=\"UTF-8\">\n"
                    "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
                    "    <title>Athena - The Amazing Dog</title>\n"
                    "    <link rel=\"stylesheet\" href=\"style.css\">\n"
                    "</head>\n"
                    "<body>\n"
                    "    <div class=\"container\">\n"
                    "        <header>\n"
                    "            <h1>Athena</h1>\n"
                    "            <p class=\"subtitle\">The Most Wonderful Dog</p>\n"
                    "        </header>\n"
                    "        \n"
                    "        <div class=\"dog-profile\">\n"
                    "            <div class=\"dog-image\">\n"
                    "                <img src=\"/static/vibes/vibe-slug/athena_dog.png\" alt=\"A cute golden retriever dog named Athena\" class=\"dog-photo\">\n"
                    "            </div>\n"
                    "            \n"
                    "            <div class=\"dog-info\">\n"
                    "                <h2>About Athena</h2>\n"
                    "                <p>Athena is an amazing dog who brings joy and happiness to everyone around her. She's playful, loyal, and incredibly smart!</p>\n"
                    "                \n"
                    "                <div class=\"dog-stats\">\n"
                    "                    <div class=\"stat\">\n"
                    "                        <span class=\"stat-label\">Cuteness</span>\n"
                    "                        <div class=\"stat-bar\">\n"
                    "                            <div class=\"stat-fill\" style=\"width: 100%;\"></div>\n"
                    "                        </div>\n"
                    "                    </div>\n"
                    "                    <div class=\"stat\">\n"
                    "                        <span class=\"stat-label\">Playfulness</span>\n"
                    "                        <div class=\"stat-bar\">\n"
                    "                            <div class=\"stat-fill\" style=\"width: 95%;\"></div>\n"
                    "                        </div>\n"
                    "                    </div>\n"
                    "                    <div class=\"stat\">\n"
                    "                        <span class=\"stat-label\">Loyalty</span>\n"
                    "                        <div class=\"stat-bar\">\n"
                    "                            <div class=\"stat-fill\" style=\"width: 100%;\"></div>\n"
                    "                        </div>\n"
                    "                    </div>\n"
                    "                    <div class=\"stat\">\n"
                    "                        <span class=\"stat-label\">Intelligence</span>\n"
                    "                        <div class=\"stat-bar\">\n"
                    "                            <div class=\"stat-fill\" style=\"width: 90%;\"></div>\n"
                    "                        </div>\n"
                    "                    </div>\n"
                    "                </div>\n"
                    "            </div>\n"
                    "        </div>\n"
                    "        \n"
                    "        <div class=\"dog-gallery\">\n"
                    "            <h2>Athena's Favorite Activities</h2>\n"
                    "            <div class=\"activities\">\n"
                    "                <div class=\"activity\">\n"
                    "                    <div class=\"activity-icon\">🦴</div>\n"
                    "                    <p>Chewing Bones</p>\n"
                    "                </div>\n"
                    "                <div class=\"activity\">\n"
                    "                    <div class=\"activity-icon\">🏃‍♀️</div>\n"
                    "                    <p>Running</p>\n"
                    "                </div>\n"
                    "                <div class=\"activity\">\n"
                    "                    <div class=\"activity-icon\">🎾</div>\n"
                    "                    <p>Fetching Balls</p>\n"
                    "                </div>\n"
                    "                <div class=\"activity\">\n"
                    "                    <div class=\"activity-icon\">😴</div>\n"
                    "                    <p>Napping</p>\n"
                    "                </div>\n"
                    "            </div>\n"
                    "        </div>\n"
                    "        \n"
                    "        <footer>\n"
                    "            <p>Made with ❤️ for Athena</p>\n"
                    "            <button id=\"treat-button\">Give Athena a Treat!</button>\n"
                    "        </footer>\n"
                    "    </div>\n"
                    "    <script src=\"script.js\"></script>\n"
                    "</body>\n"
                    "</html>\n"
                    "```\n\n"
                    "Now I'll create a style.css file to make Athena's page look beautiful:\n\n"
                    "```tool\n"
                    "write_file\n"
                    "filename: style.css\n"
                    "content:\n"
                    "* {\n"
                    "    box-sizing: border-box;\n"
                    "    margin: 0;\n"
                    "    padding: 0;\n"
                    "}\n"
                    "\n"
                    "body {\n"
                    "    font-family: 'Arial', sans-serif;\n"
                    "    background-color: #f8f9fa;\n"
                    "    color: #333;\n"
                    "    line-height: 1.6;\n"
                    "}\n"
                    "\n"
                    ".container {\n"
                    "    max-width: 1000px;\n"
                    "    margin: 0 auto;\n"
                    "    padding: 20px;\n"
                    "}\n"
                    "\n"
                    "header {\n"
                    "    text-align: center;\n"
                    "    margin-bottom: 40px;\n"
                    "    padding: 20px;\n"
                    "    background-color: #6a5acd;\n"
                    "    color: white;\n"
                    "    border-radius: 10px;\n"
                    "    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);\n"
                    "}\n"
                    "\n"
                    "h1 {\n"
                    "    font-size: 3rem;\n"
                    "    margin-bottom: 10px;\n"
                    "}\n"
                    "\n"
                    ".subtitle {\n"
                    "    font-size: 1.2rem;\n"
                    "    font-style: italic;\n"
                    "}\n"
                    "\n"
                    ".dog-profile {\n"
                    "    display: flex;\n"
                    "    flex-wrap: wrap;\n"
                    "    gap: 30px;\n"
                    "    margin-bottom: 40px;\n"
                    "    background-color: white;\n"
                    "    padding: 30px;\n"
                    "    border-radius: 10px;\n"
                    "    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);\n"
                    "}\n"
                    "\n"
                    ".dog-image {\n"
                    "    flex: 1;\n"
                    "    min-width: 300px;\n"
                    "    display: flex;\n"
                    "    justify-content: center;\n"
                    "    align-items: center;\n"
                    "}\n"
                    "\n"
                    ".dog-photo {\n"
                    "    max-width: 100%;\n"
                    "    height: auto;\n"
                    "    border-radius: 10px;\n"
                    "    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);\n"
                    "}\n"
                    "\n"
                    ".dog-info {\n"
                    "    flex: 2;\n"
                    "    min-width: 300px;\n"
                    "}\n"
                    "\n"
                    ".dog-info h2 {\n"
                    "    margin-bottom: 15px;\n"
                    "    color: #6a5acd;\n"
                    "}\n"
                    "\n"
                    ".dog-info p {\n"
                    "    margin-bottom: 20px;\n"
                    "}\n"
                    "\n"
                    ".dog-stats {\n"
                    "    margin-top: 20px;\n"
                    "}\n"
                    "\n"
                    ".stat {\n"
                    "    margin-bottom: 15px;\n"
                    "}\n"
                    "\n"
                    ".stat-label {\n"
                    "    display: block;\n"
                    "    margin-bottom: 5px;\n"
                    "    font-weight: bold;\n"
                    "}\n"
                    "\n"
                    ".stat-bar {\n"
                    "    height: 10px;\n"
                    "    background-color: #e0e0e0;\n"
                    "    border-radius: 5px;\n"
                    "    overflow: hidden;\n"
                    "}\n"
                    "\n"
                    ".stat-fill {\n"
                    "    height: 100%;\n"
                    "    background-color: #6a5acd;\n"
                    "    border-radius: 5px;\n"
                    "}\n"
                    "\n"
                    ".dog-gallery {\n"
                    "    margin-bottom: 40px;\n"
                    "    background-color: white;\n"
                    "    padding: 30px;\n"
                    "    border-radius: 10px;\n"
                    "    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);\n"
                    "}\n"
                    "\n"
                    ".dog-gallery h2 {\n"
                    "    margin-bottom: 20px;\n"
                    "    color: #6a5acd;\n"
                    "    text-align: center;\n"
                    "}\n"
                    "\n"
                    ".activities {\n"
                    "    display: flex;\n"
                    "    flex-wrap: wrap;\n"
                    "    justify-content: space-around;\n"
                    "    gap: 20px;\n"
                    "}\n"
                    "\n"
                    ".activity {\n"
                    "    text-align: center;\n"
                    "    width: 120px;\n"
                    "}\n"
                    "\n"
                    ".activity-icon {\n"
                    "    font-size: 3rem;\n"
                    "    margin-bottom: 10px;\n"
                    "}\n"
                    "\n"
                    "footer {\n"
                    "    text-align: center;\n"
                    "    padding: 20px;\n"
                    "    background-color: #6a5acd;\n"
                    "    color: white;\n"
                    "    border-radius: 10px;\n"
                    "    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);\n"
                    "}\n"
                    "\n"
                    "#treat-button {\n"
                    "    margin-top: 15px;\n"
                    "    padding: 10px 20px;\n"
                    "    background-color: #ff6b6b;\n"
                    "    color: white;\n"
                    "    border: none;\n"
                    "    border-radius: 5px;\n"
                    "    cursor: pointer;\n"
                    "    font-size: 1rem;\n"
                    "    transition: background-color 0.3s;\n"
                    "}\n"
                    "\n"
                    "#treat-button:hover {\n"
                    "    background-color: #ff5252;\n"
                    "}\n"
                    "\n"
                    "@media (max-width: 768px) {\n"
                    "    .dog-profile {\n"
                    "        flex-direction: column;\n"
                    "    }\n"
                    "    \n"
                    "    .dog-image {\n"
                    "        margin-bottom: 20px;\n"
                    "    }\n"
                    "}\n"
                    "```\n\n"
                    "Finally, I'll create a script.js file to add some interactivity:\n\n"
                    "```tool\n"
                    "write_file\n"
                    "filename: script.js\n"
                    "content:\n"
                    "document.addEventListener('DOMContentLoaded', function() {\n"
                    "    const treatButton = document.getElementById('treat-button');\n"
                    "    let treatCount = 0;\n"
                    "    \n"
                    "    treatButton.addEventListener('click', function() {\n"
                    "        treatCount++;\n"
                    "        \n"
                    "        // Create a treat element\n"
                    "        const treat = document.createElement('div');\n"
                    "        treat.className = 'treat';\n"
                    "        treat.textContent = '🦴';\n"
                    "        treat.style.position = 'fixed';\n"
                    "        treat.style.fontSize = '2rem';\n"
                    "        treat.style.left = Math.random() * 80 + 10 + '%';\n"
                    "        treat.style.top = '-50px';\n"
                    "        treat.style.transition = 'top 1s ease-in, transform 1s ease-in';\n"
                    "        treat.style.zIndex = '1000';\n"
                    "        document.body.appendChild(treat);\n"
                    "        \n"
                    "        // Animate the treat falling\n"
                    "        setTimeout(() => {\n"
                    "            treat.style.top = '110%';\n"
                    "            treat.style.transform = 'rotate(' + (Math.random() * 360) + 'deg)';\n"
                    "        }, 50);\n"
                    "        \n"
                    "        // Remove the treat after animation\n"
                    "        setTimeout(() => {\n"
                    "            document.body.removeChild(treat);\n"
                    "        }, 1500);\n"
                    "        \n"
                    "        // Update button text\n"
                    "        treatButton.textContent = `Given ${treatCount} treat${treatCount !== 1 ? 's' : ''}`;\n"
                    "        \n"
                    "        // Add a bark sound\n"
                    "        const bark = new Audio('data:audio/wav;base64,UklGRjIAAABXQVZFZm10IBIAAAABAAEAQB8AAEAfAAABAAgAAABMYXZjNTguMTMuMTAwAGJhcmsud2F2ZQ==');\n"
                    "        bark.play().catch(e => console.log('Audio play failed:', e));\n"
                    "    });\n"
                    "});\n"
                    "```\n\n"
                    "I've created three files for Athena's page:"
                )
                self.add_message("assistant", mock_content)

                # Process the tool call to get the actual file list
                processed_content = self.process_tool_calls(mock_content)

                # Return the processed content
                return {
                    "success": True,
                    "content": processed_content,
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

            elif tool_name == "generate_image":
                # Generate an image using DALL-E
                from .image_utils import generate_image, save_generated_image

                prompt = None
                size = "1024x1024"
                quality = "standard"
                filename = None

                for line in lines[1:]:
                    if line.startswith("prompt:"):
                        prompt = line[len("prompt:"):].strip()
                    elif line.startswith("size:"):
                        size = line[len("size:"):].strip()
                    elif line.startswith("quality:"):
                        quality = line[len("quality:"):].strip()
                    elif line.startswith("filename:"):
                        filename = line[len("filename:"):].strip()

                if not prompt:
                    tool_result = "Error: No prompt provided for generate_image"
                else:
                    # Check if the user has an OpenAI API key
                    if not self.user.profile.chatgpt_api_key:
                        tool_result = "Error: You need to add an OpenAI API key to your profile to generate images."
                    else:
                        # Generate the image
                        api_key = self.user.profile.chatgpt_api_key
                        image_result = generate_image(api_key, prompt, size, quality)

                        if image_result.get('success', False):
                            # Get the image URL from DALL-E
                            image_url = image_result.get('image_url')
                            revised_prompt = image_result.get('revised_prompt', prompt)

                            # Generate a filename if not provided
                            if not filename:
                                import uuid
                                filename = f"dalle_{uuid.uuid4()}.png"

                            # Make sure the filename has an image extension
                            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                                filename += '.png'

                            # Save the image directly to the vibe directory
                            save_result = file_manager.save_image(image_url, filename)

                            if save_result.get('success', False):
                                # Also save to the database for tracking
                                save_db_result = save_generated_image(
                                    user=self.user,
                                    prompt=prompt,
                                    image_url=image_url,
                                    revised_prompt=revised_prompt
                                )

                                if save_db_result.get('success', False):
                                    # Associate the image with the vibe
                                    from .models import GeneratedImage
                                    image = GeneratedImage.objects.get(id=save_db_result.get('image_id'))
                                    image.vibe = self.vibe
                                    image.save()

                                # Return the local path for use in HTML
                                image_path = save_result.get('url')
                                tool_result = f"Image generated and saved to the vibe folder!\n\nFilename: {filename}\n\nLocal path: {image_path}\n\nRevised prompt: {revised_prompt}\n\nYou can include this image in your HTML using:\n\n```html\n<img src=\"{image_path}\" alt=\"{prompt}\" class=\"generated-image\">\n```"
                            else:
                                tool_result = f"Error: {save_result.get('error', 'Failed to save the generated image to the vibe folder.')}"
                        else:
                            tool_result = f"Error: {image_result.get('error', 'Failed to generate image.')}"

            elif tool_name == "save_image":
                # Save an image from a URL to the vibe directory
                from .file_utils import VibeFileManager

                url = None
                filename = None

                for line in lines[1:]:
                    if line.startswith("url:"):
                        url = line[len("url:"):].strip()
                    elif line.startswith("filename:"):
                        filename = line[len("filename:"):].strip()

                if not url:
                    tool_result = "Error: No URL provided for save_image"
                else:
                    # Save the image
                    result_dict = file_manager.save_image(url, filename)

                    if result_dict.get('success', False):
                        image_path = result_dict.get('url')
                        tool_result = f"Image saved successfully!\n\nImage path: {image_path}\n\nYou can include this image in your HTML using:\n\n```html\n<img src=\"{image_path}\" alt=\"Image\" class=\"saved-image\">\n```"
                    else:
                        tool_result = f"Error: {result_dict.get('error', 'Failed to save the image.')}"

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
