"""
Conversation management for AI assistants.
"""
import logging
from typing import Dict, List, Any
from django.contrib.auth.models import User

from .ai_models import get_user_ai_context
from .ai_prompts import VIBE_BUILDER_SYSTEM_PROMPT, get_vibe_context_prompt
from .ai_tools import process_tool_calls

logger = logging.getLogger(__name__)

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
                "content": VIBE_BUILDER_SYSTEM_PROMPT
            }
        ]

        # Add initial context about the vibe
        self.add_message(
            "system",
            get_vibe_context_prompt(
                self.vibe.title,
                self.vibe.description,
                self.vibe.slug
            )
        )

    def add_message(self, role: str, content: str) -> None:
        """
        Add a message to the conversation.

        Args:
            role: The role of the message sender (system, user, assistant)
            content: The content of the message
        """
        self.messages.append({"role": role, "content": content})

    def get_response(self, temperature: float = 0.7, max_tokens: int = 1000, max_iterations: int = 5) -> Dict[str, Any]:
        """
        Get a response from the AI using the O1 reasoning loop.

        This method implements a proper O1 reasoning loop that allows the AI to:
        1. Think about what it needs to do
        2. Use tools to gather information or make changes
        3. Analyze the results of tool calls
        4. Decide what to do next based on those results
        5. Repeat until the task is complete

        Args:
            temperature: Controls randomness (0-1)
            max_tokens: Maximum number of tokens to generate
            max_iterations: Maximum number of iterations in the reasoning loop

        Returns:
            Dictionary with response content or error message
        """
        try:
            if not self.context:
                logger.error("No OpenAI API key found for this user")
                return {"success": False, "error": "No OpenAI API key found for this user"}

            # For testing purposes, if the API key is a test key, return a mock response
            if self.context.api_key == 'sk-test-key':
                # Log that we're using a mock response
                logger.warning(f"Using mock response because API key is 'sk-test-key'")

                # Create a mock response that demonstrates proper tool usage with O1 reasoning
                from .ai_mock_responses import get_mock_response
                mock_content = get_mock_response()
                self.add_message("assistant", mock_content)

                # Process the tool call to get the actual file list
                processed_content = process_tool_calls(mock_content, self.vibe, self.user)

                # Return the processed content
                return {
                    "success": True,
                    "content": processed_content,
                    "raw_response": {"choices": [{"message": {"content": mock_content}}]}
                }

            # Log the actual API key (first 5 chars) for debugging
            logger.info(f"Using API key: {self.context.api_key[:5]}...")

            # Log the messages being sent to the API
            logger.info(f"Starting O1 reasoning loop with {len(self.messages)} messages")
            for i, msg in enumerate(self.messages):
                logger.info(f"Message {i}: role={msg['role']}, content_length={len(msg['content'])}")

            # Initialize variables for the reasoning loop
            iteration = 0
            final_content = ""
            all_tool_results = []
            has_tool_calls = False
            final_response = None

            # Start the O1 reasoning loop
            while iteration < max_iterations:
                iteration += 1
                logger.info(f"O1 reasoning loop iteration {iteration}/{max_iterations}")

                # Generate the response
                logger.info(f"Generating response with temperature={temperature}, max_tokens={max_tokens}")
                response = self.context.generate_response(self.messages, temperature, max_tokens)

                # Log the response
                logger.info(f"Response received: {response.keys()}")
                if "error" in response:
                    logger.error(f"Error in response: {response['error']}")
                    return {"success": False, "error": response["error"]}

                # Save the final response
                final_response = response

                # Extract the content
                content = self.context.extract_content(response)
                logger.info(f"Extracted content length: {len(content)}")

                # Check if there are tool calls in the response
                tool_calls = []
                if "choices" in response and "message" in response["choices"][0]:
                    message = response["choices"][0]["message"]
                    if "tool_calls" in message:
                        tool_calls = message["tool_calls"]
                        has_tool_calls = True
                        logger.info(f"Tool calls found: {len(tool_calls)}")
                        for i, tool_call in enumerate(tool_calls):
                            function = tool_call.get("function", {})
                            logger.info(f"Tool call {i}: name={function.get('name')}")
                    else:
                        logger.info("No tool calls found in the response")

                # If there are no tool calls, we're done with the reasoning loop
                if not tool_calls:
                    logger.info("No tool calls found, ending reasoning loop")
                    final_content = content
                    break

                # Process tool calls in the response
                processed_content = process_tool_calls(content, self.vibe, self.user)
                logger.info(f"Processed content length: {len(processed_content)}")

                # Add the assistant's response to the conversation history
                self.add_message("assistant", content)
                logger.info("Added assistant response to conversation history")

                # Extract tool results from the processed content
                tool_results = []
                for tool_call in tool_calls:
                    function = tool_call.get("function", {})
                    name = function.get("name", "")
                    tool_id = tool_call.get("id", "")

                    # Find the tool result in the processed content
                    tool_result_start = processed_content.find(f"Tool result:")
                    if tool_result_start != -1:
                        tool_result_end = processed_content.find("\n\n", tool_result_start)
                        if tool_result_end == -1:
                            tool_result_end = len(processed_content)

                        tool_result = processed_content[tool_result_start:tool_result_end].strip()
                        tool_results.append({
                            "tool_call_id": tool_id,
                            "role": "tool",
                            "name": name,
                            "content": tool_result
                        })

                        logger.info(f"Extracted tool result for {name}: {tool_result[:100]}...")

                # Add tool results to all_tool_results
                all_tool_results.extend(tool_results)

                # Add tool results to the conversation history
                for tool_result in tool_results:
                    self.add_message("tool", tool_result["content"])
                    logger.info(f"Added tool result to conversation history: {tool_result['name']}")

                # If we've reached the maximum number of iterations, break
                if iteration >= max_iterations:
                    logger.warning(f"Reached maximum number of iterations ({max_iterations}), ending reasoning loop")
                    final_content = processed_content
                    break

            # If we didn't have any tool calls, just return the original content
            if not has_tool_calls:
                logger.info("No tool calls were made during the reasoning loop")
                return {
                    "success": True,
                    "content": content,
                    "raw_response": final_response
                }

            # Process the final content with all tool results
            final_processed_content = process_tool_calls(final_content, self.vibe, self.user)
            logger.info(f"Final processed content length: {len(final_processed_content)}")

            return {
                "success": True,
                "content": final_processed_content,
                "raw_response": final_response,
                "tool_results": all_tool_results,
                "iterations": iteration
            }
        except Exception as e:
            logger.exception(f"Error in O1 reasoning loop: {str(e)}")
            return {
                "success": False,
                "error": f"Error in O1 reasoning loop: {str(e)}"
            }


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
    from .ai_prompts import CONTENT_GENERATION_PROMPT

    context = get_user_ai_context(user)
    if not context:
        return {"error": "No OpenAI API key found for this user"}

    messages = [
        {"role": "system", "content": CONTENT_GENERATION_PROMPT},
        {"role": "user", "content": f"Generate content for my vibe titled '{vibe_title}'. Description: {vibe_description}. Please provide: 1) A short tagline, 2) Three key elements that define this vibe, 3) A color palette suggestion (with hex codes), and 4) A short paragraph expanding on the vibe's essence."}
    ]

    response = context.generate_response(messages)
    content = context.extract_content(response)

    return {
        "success": "error" not in response,
        "content": content,
        "raw_response": response
    }
