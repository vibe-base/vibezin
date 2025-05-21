"""
Views for AI-related functionality.
"""
import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.urls import reverse
from .models import Vibe, VibeConversationHistory
from .ai_utils import VibeConversation
from .file_utils import VibeFileManager

logger = logging.getLogger(__name__)

@login_required
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
    
    # Get the message from the request
    try:
        data = json.loads(request.body)
        message = data.get('message', '').strip()
        
        if not message:
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
    
    # Create a conversation object
    conversation = VibeConversation(request.user, vibe.id)
    
    # Load the conversation history
    for msg in conversation_history.conversation:
        if msg['role'] != 'system':  # Skip system messages as they're added by the VibeConversation class
            conversation.add_message(msg['role'], msg['content'])
    
    # Get a response from the AI
    response = conversation.get_response()
    
    if response.get('success', False):
        # Add the AI's response to the conversation history
        conversation_history.add_message('assistant', response['content'])
        
        return JsonResponse({
            'success': True,
            'message': response['content']
        })
    else:
        return JsonResponse({
            'success': False,
            'error': response.get('error', "Unknown error")
        })


@login_required
@require_POST
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
        data = json.loads(request.body)
        operation = data.get('operation', '').strip()
        filename = data.get('filename', '').strip()
        content = data.get('content', '')
        
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
            if filename.endswith('.html'):
                vibe.has_custom_html = True
            elif filename.endswith('.css'):
                vibe.has_custom_css = True
            elif filename.endswith('.js'):
                vibe.has_custom_js = True
            vibe.save()
    elif operation == 'delete':
        result = file_manager.delete_file(filename)
    elif operation == 'diff':
        result = file_manager.get_diff(filename, content)
    elif operation == 'list':
        result = {
            'success': True,
            'files': file_manager.list_files()
        }
    else:
        result = {
            'success': False,
            'error': f"Unknown operation: {operation}"
        }
    
    return JsonResponse(result)
