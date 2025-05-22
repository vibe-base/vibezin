"""
Views for AI-related functionality.
"""
import json
import os
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.urls import reverse
from .models import Vibe, VibeConversationHistory
from .ai_conversation import VibeConversation
from .file_utils import VibeFileManager

logger = logging.getLogger(__name__)

@login_required
@ensure_csrf_cookie
def vibe_ai_builder(request, vibe_slug):
    """
    View for the AI builder interface for a vibe.

    Args:
        request: The HTTP request
        vibe_slug: The slug of the vibe

    Returns:
        Rendered template
    """
    # Get the vibe
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Check if the user is the owner of the vibe
    if vibe.user != request.user:
        messages.error(request, "You don't have permission to edit this vibe.")
        return redirect('vibezin:vibe_detail_by_slug', vibe_slug=vibe_slug)

    # Check if the user has an OpenAI API key
    if not hasattr(request.user, 'profile') or not request.user.profile.chatgpt_api_key:
        messages.error(request, "You need to add an OpenAI API key to your profile to use the AI builder.")
        return redirect('vibezin:edit_profile')

    # Get or create a conversation history
    conversation_history, created = VibeConversationHistory.objects.get_or_create(
        vibe=vibe,
        user=request.user,
        defaults={
            'conversation': []
        }
    )

    # Get the file manager
    file_manager = VibeFileManager(vibe)

    # Get the list of files
    files = file_manager.list_files()

    context = {
        'vibe': vibe,
        'title': f"AI Builder - {vibe.title}",
        'conversation_history': conversation_history,
        'files': files
    }

    return render(request, 'vibezin/vibe_ai_builder.html', context)


@login_required
@require_POST
@ensure_csrf_cookie
def vibe_ai_clear_conversation(request, vibe_slug):
    """
    API endpoint for clearing the conversation history.

    Args:
        request: The HTTP request
        vibe_slug: The slug of the vibe

    Returns:
        JSON response with success status
    """
    # Get the vibe
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Check if the user is the owner of the vibe
    if vibe.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this vibe.")

    # Get the conversation history
    try:
        conversation_history = VibeConversationHistory.objects.get(
            vibe=vibe,
            user=request.user
        )

        # Clear the conversation
        conversation_history.conversation = []
        conversation_history.message_count = 0
        conversation_history.save()

        logger.info(f"Cleared conversation history for vibe {vibe_slug}")

        return JsonResponse({
            'success': True,
            'message': "Conversation history cleared."
        })
    except VibeConversationHistory.DoesNotExist:
        logger.warning(f"No conversation history found for vibe {vibe_slug}")
        return JsonResponse({
            'success': True,
            'message': "No conversation history found."
        })
    except Exception as e:
        logger.exception(f"Error clearing conversation history: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error clearing conversation history: {str(e)}"
        })

@login_required
@require_POST
@ensure_csrf_cookie
def vibe_ai_message(request, vibe_slug):
    """
    API endpoint for sending a message to the AI.

    Args:
        request: The HTTP request
        vibe_slug: The slug of the vibe

    Returns:
        JSON response with the AI's reply
    """
    # Get the vibe
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Check if the user is the owner of the vibe
    if vibe.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this vibe.")

    # Check if the user has an OpenAI API key
    if not hasattr(request.user, 'profile') or not request.user.profile.chatgpt_api_key:
        return JsonResponse({
            'success': False,
            'error': "You need to add an OpenAI API key to your profile to use the AI builder."
        })

    # Debug info
    logger.info(f"Received AI message request for vibe: {vibe_slug}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")

    # Get the message from the request
    try:
        # First try to get the message from POST data
        message = request.POST.get('message', '').strip()

        # If not in POST data, try to parse JSON
        if not message and request.content_type == 'application/json':
            try:
                # Use getattr to safely access request.body_decoded if it exists
                # This is to avoid the RawPostDataException
                if hasattr(request, '_body'):
                    # If _body exists, use it directly
                    data = json.loads(request._body.decode('utf-8'))
                else:
                    # Otherwise, read the body once
                    body = request.body.decode('utf-8')
                    data = json.loads(body)

                message = data.get('message', '').strip()
                logger.info(f"Parsed message from JSON: {message}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {str(e)}")
                # If JSON parsing fails, the body might be form data
                logger.info("JSON parsing failed, body might be form data")

        logger.info(f"Final message: {message}")

        if not message:
            logger.warning("Empty message received")
            return JsonResponse({
                'success': False,
                'error': "Message cannot be empty."
            })
    except Exception as e:
        logger.exception(f"Error parsing message: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error parsing message: {str(e)}"
        })

    # Get or create a conversation history
    conversation_history, created = VibeConversationHistory.objects.get_or_create(
        vibe=vibe,
        user=request.user,
        defaults={
            'conversation': []
        }
    )

    # Add the user's message to the conversation history
    conversation_history.add_message('user', message)
    logger.info(f"Added user message to conversation history: {message[:50]}...")

    # Create a conversation object
    try:
        logger.info(f"Creating conversation object for user {request.user.username} and vibe {vibe.id}")
        conversation = VibeConversation(request.user, vibe.id)

        # Load the conversation history
        logger.info(f"Loading conversation history with {len(conversation_history.conversation)} messages")
        for i, msg in enumerate(conversation_history.conversation):
            if msg['role'] != 'system':  # Skip system messages as they're added by the VibeConversation class
                logger.info(f"Adding message {i} to conversation: role={msg['role']}, content_length={len(msg['content'])}")
                conversation.add_message(msg['role'], msg['content'])

        # Get a response from the AI using the O1 reasoning loop
        logger.info("Getting response from AI using O1 reasoning loop")
        response = conversation.get_response(max_iterations=5)  # Allow up to 5 iterations in the reasoning loop

        # Log the response details
        logger.info(f"AI response received: success={response.get('success', False)}")
        if 'iterations' in response:
            logger.info(f"O1 reasoning loop completed in {response['iterations']} iterations")
        if 'tool_results' in response:
            logger.info(f"O1 reasoning loop used {len(response.get('tool_results', []))} tool calls")
    except Exception as e:
        logger.exception(f"Error in AI conversation: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error in AI conversation: {str(e)}"
        })

    if response.get('success', False):
        # Add the AI's response to the conversation history
        # Note: We store the original content, not the processed content
        logger.info(f"Adding AI response to conversation history: content_length={len(response['content'])}")
        conversation_history.add_message('assistant', response['content'])

        # Save the conversation history
        logger.info("Saving conversation history")
        conversation_history.save()

        # Log the conversation history after saving
        logger.info(f"Conversation history now has {len(conversation_history.conversation)} messages")
        for i, msg in enumerate(conversation_history.conversation[-2:]):  # Log the last 2 messages
            logger.info(f"Last message {i}: role={msg['role']}, content_length={len(msg['content'])}")

        # Return the processed content to the client with O1 reasoning information
        # This includes the results of any tool calls and information about the reasoning process
        logger.info(f"Returning processed content to client: content_length={len(response.get('content', ''))}")

        # Include information about the O1 reasoning process in the response
        result = {
            'success': True,
            'message': response.get('content', response['content']),
            'o1_reasoning': {
                'iterations': response.get('iterations', 0),
                'tool_calls_count': len(response.get('tool_results', [])),
                'completed': True
            }
        }

        logger.info(f"Returning successful response with O1 reasoning info: iterations={result['o1_reasoning']['iterations']}, tool_calls={result['o1_reasoning']['tool_calls_count']}")
        return JsonResponse(result)
    else:
        return JsonResponse({
            'success': False,
            'error': response.get('error', "Unknown error")
        })


@login_required
@require_POST
@ensure_csrf_cookie
def vibe_ai_file_operation(request, vibe_slug):
    """
    API endpoint for file operations.

    Args:
        request: The HTTP request
        vibe_slug: The slug of the vibe

    Returns:
        JSON response with the result of the operation
    """
    # Get the vibe
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Check if the user is the owner of the vibe
    if vibe.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this vibe.")

    # Get the operation and file information from the request
    try:
        # First try to get data from POST
        operation = request.POST.get('operation', '').strip()
        filename = request.POST.get('filename', '').strip()
        content = request.POST.get('content', '')

        # If not in POST data, try to parse JSON
        if not operation and request.content_type == 'application/json':
            try:
                # Use getattr to safely access request.body_decoded if it exists
                # This is to avoid the RawPostDataException
                if hasattr(request, '_body'):
                    # If _body exists, use it directly
                    data = json.loads(request._body.decode('utf-8'))
                else:
                    # Otherwise, read the body once
                    body = request.body.decode('utf-8')
                    data = json.loads(body)

                operation = data.get('operation', '').strip()
                filename = data.get('filename', '').strip()
                content = data.get('content', '')
                logger.info(f"Parsed operation from JSON: {operation}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {str(e)}")
                # If JSON parsing fails, the body might be form data
                logger.info("JSON parsing failed, body might be form data")

        logger.info(f"Final operation: {operation}, filename: {filename}")

        if not operation:
            return JsonResponse({
                'success': False,
                'error': "Operation cannot be empty."
            })

        if not filename and operation != 'list':
            return JsonResponse({
                'success': False,
                'error': "Filename cannot be empty."
            })
    except Exception as e:
        logger.exception(f"Error parsing file operation: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error parsing file operation: {str(e)}"
        })

    # Get the file manager
    file_manager = VibeFileManager(vibe)

    # Perform the operation
    if operation == 'read':
        result = file_manager.read_file(filename)
    elif operation == 'write':
        result = file_manager.write_file(filename, content)

        # Update the vibe's custom file flags
        if result.get('success', False):
            logger.info(f"File write successful: {filename}")
            logger.info(f"Vibe custom flags before update - HTML: {vibe.has_custom_html}, CSS: {vibe.has_custom_css}, JS: {vibe.has_custom_js}")

            if filename.endswith('.html'):
                logger.info(f"Setting has_custom_html to True for file: {filename}")
                vibe.has_custom_html = True
            elif filename.endswith('.css'):
                logger.info(f"Setting has_custom_css to True for file: {filename}")
                vibe.has_custom_css = True
            elif filename.endswith('.js'):
                logger.info(f"Setting has_custom_js to True for file: {filename}")
                vibe.has_custom_js = True

            vibe.save()
            logger.info(f"Vibe custom flags after update - HTML: {vibe.has_custom_html}, CSS: {vibe.has_custom_css}, JS: {vibe.has_custom_js}")
    elif operation == 'delete':
        result = file_manager.delete_file(filename)
    elif operation == 'diff':
        result = file_manager.get_diff(filename, content)
    elif operation == 'list':
        logger.error(f"CRITICAL DEBUG: list operation called for vibe: {vibe.slug}")

        # Get the list of files
        files = file_manager.list_files()
        logger.error(f"CRITICAL DEBUG: Got {len(files)} files from file_manager.list_files()")

        # Also list the files directly using os.listdir for debugging
        try:
            vibe_dir = file_manager.vibe_dir
            logger.error(f"CRITICAL DEBUG: Vibe directory: {vibe_dir}")
            logger.error(f"CRITICAL DEBUG: Vibe directory exists: {vibe_dir.exists()}")

            if vibe_dir.exists():
                logger.error(f"CRITICAL DEBUG: Files in directory using os.listdir:")
                for filename in os.listdir(str(vibe_dir)):
                    logger.error(f"CRITICAL DEBUG: - {filename}")
        except Exception as e:
            logger.error(f"CRITICAL DEBUG: Error listing directory with os.listdir: {str(e)}")

        result = {
            'success': True,
            'files': files
        }
    else:
        result = {
            'success': False,
            'error': f"Unknown operation: {operation}"
        }

    return JsonResponse(result)


@login_required
@require_POST
def enable_custom_html(request, vibe_slug):
    """
    API endpoint to enable custom HTML for a vibe.

    Args:
        request: The HTTP request
        vibe_slug: The slug of the vibe

    Returns:
        JSON response with the result of the operation
    """
    # Get the vibe
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Check if the user is the owner of the vibe
    if vibe.user != request.user:
        return JsonResponse({
            'success': False,
            'error': "You don't have permission to edit this vibe."
        })

    try:
        # Set the custom HTML flag to True
        vibe.has_custom_html = True
        vibe.save()

        logger.info(f"Custom HTML enabled for vibe: {vibe.slug}")

        return JsonResponse({
            'success': True,
            'message': "Custom HTML enabled for this vibe."
        })
    except Exception as e:
        logger.exception(f"Error enabling custom HTML: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error enabling custom HTML: {str(e)}"
        })


@login_required
@require_POST
@ensure_csrf_cookie
def vibe_ai_create_file(request, vibe_slug):
    """
    API endpoint for creating a file directly from the AI conversation.
    This is a simplified endpoint that bypasses the AI conversation and directly creates a file.

    Args:
        request: The HTTP request
        vibe_slug: The slug of the vibe

    Returns:
        JSON response with the result of the operation
    """
    # Get the vibe
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Check if the user is the owner of the vibe
    if vibe.user != request.user:
        return HttpResponseForbidden("You don't have permission to edit this vibe.")

    # Get the filename and content from the request
    try:
        # First try to get data from POST
        filename = request.POST.get('filename', '').strip()
        content = request.POST.get('content', '')

        # If not in POST data, try to parse JSON
        if not filename and request.content_type == 'application/json':
            try:
                # Use getattr to safely access request.body_decoded if it exists
                # This is to avoid the RawPostDataException
                if hasattr(request, '_body'):
                    # If _body exists, use it directly
                    data = json.loads(request._body.decode('utf-8'))
                else:
                    # Otherwise, read the body once
                    body = request.body.decode('utf-8')
                    data = json.loads(body)

                filename = data.get('filename', '').strip()
                content = data.get('content', '')
                logger.info(f"Parsed filename from JSON: {filename}")
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode error: {str(e)}")
                # If JSON parsing fails, the body might be form data
                logger.info("JSON parsing failed, body might be form data")

        logger.info(f"Creating file: {filename}")

        if not filename:
            return JsonResponse({
                'success': False,
                'error': "Filename cannot be empty."
            })

        if not content:
            return JsonResponse({
                'success': False,
                'error': "Content cannot be empty."
            })
    except Exception as e:
        logger.exception(f"Error parsing file creation request: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error parsing file creation request: {str(e)}"
        })

    # Get the file manager
    file_manager = VibeFileManager(vibe)

    # Create the file
    try:
        # Get the file path
        file_path = file_manager.get_file_path(filename)
        logger.info(f"File path: {file_path}")

        # Write the file directly first
        with open(file_path, 'w') as f:
            f.write(content)

        logger.info(f"File written directly: {file_path}")

        # Now use the file manager to handle backups, etc.
        result = file_manager.write_file(filename, content)
        logger.info(f"File manager result: {result}")

        # Update the vibe's custom file flags
        if result.get('success', False):
            logger.info(f"File write successful: {filename}")
            logger.info(f"Vibe custom flags before update - HTML: {vibe.has_custom_html}, CSS: {vibe.has_custom_css}, JS: {vibe.has_custom_js}")

            if filename.endswith('.html'):
                logger.info(f"Setting has_custom_html to True for file: {filename}")
                vibe.has_custom_html = True
            elif filename.endswith('.css'):
                logger.info(f"Setting has_custom_css to True for file: {filename}")
                vibe.has_custom_css = True
            elif filename.endswith('.js'):
                logger.info(f"Setting has_custom_js to True for file: {filename}")
                vibe.has_custom_js = True

            vibe.save()
            logger.info(f"Vibe custom flags after update - HTML: {vibe.has_custom_html}, CSS: {vibe.has_custom_css}, JS: {vibe.has_custom_js}")

            # Verify the file exists
            if file_path.exists():
                logger.info(f"File exists after creation: {file_path}")
                logger.info(f"File size: {file_path.stat().st_size} bytes")
            else:
                logger.error(f"File does not exist after creation: {file_path}")
                return JsonResponse({
                    'success': False,
                    'error': f"File was not created: {filename}"
                })

            return JsonResponse({
                'success': True,
                'message': f"File created: {filename}",
                'path': str(file_path),
                'name': file_path.name
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', "Unknown error")
            })
    except Exception as e:
        logger.exception(f"Error creating file: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error creating file: {str(e)}"
        })
