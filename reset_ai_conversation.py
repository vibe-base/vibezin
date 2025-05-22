#!/usr/bin/env python
"""
Script to reset AI conversation history and check API keys.
"""
import os
import sys
import django
import logging

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from django.contrib.auth.models import User
from vibezin.models import Vibe, VibeConversationHistory, UserProfile

def main():
    """Reset AI conversation history and check API keys."""
    # Check if a username was provided
    if len(sys.argv) > 1:
        username = sys.argv[1]
        try:
            user = User.objects.get(username=username)
            logger.info(f"Found user: {user.username}")
        except User.DoesNotExist:
            logger.error(f"User '{username}' not found.")
            return
    else:
        # Get all users
        users = User.objects.all()
        if not users:
            logger.error("No users found.")
            return
        
        # Use the first user
        user = users.first()
        logger.info(f"Using first user: {user.username}")
    
    # Check if the user has a profile
    if not hasattr(user, 'profile'):
        logger.error(f"User '{user.username}' does not have a profile.")
        return
    
    # Check if the user has an API key
    api_key = user.profile.chatgpt_api_key
    if not api_key:
        logger.error(f"User '{user.username}' does not have an API key.")
        return
    
    # Check if the API key is 'sk-test-key'
    if api_key == 'sk-test-key':
        logger.warning(f"User '{user.username}' has a test API key. This will cause mock responses to be used.")
        
        # Ask if the user wants to update the API key
        response = input("Do you want to update the API key? (y/n): ")
        if response.lower() == 'y':
            new_key = input("Enter a new API key: ")
            user.profile.chatgpt_api_key = new_key
            user.profile.save()
            logger.info(f"API key updated for user '{user.username}'.")
    else:
        logger.info(f"User '{user.username}' has a valid API key: {api_key[:5]}...")
    
    # Get all vibes for the user
    vibes = Vibe.objects.filter(user=user)
    if not vibes:
        logger.error(f"No vibes found for user '{user.username}'.")
        return
    
    # List all vibes
    logger.info(f"Found {len(vibes)} vibes for user '{user.username}':")
    for i, vibe in enumerate(vibes):
        logger.info(f"{i+1}. {vibe.title} (slug: {vibe.slug})")
    
    # Ask which vibe to reset
    vibe_index = input(f"Enter the number of the vibe to reset (1-{len(vibes)}) or 'all' for all vibes: ")
    
    if vibe_index.lower() == 'all':
        # Reset all vibes
        for vibe in vibes:
            reset_vibe_conversation(vibe, user)
    else:
        try:
            vibe_index = int(vibe_index) - 1
            if vibe_index < 0 or vibe_index >= len(vibes):
                logger.error(f"Invalid vibe index: {vibe_index + 1}")
                return
            
            vibe = vibes[vibe_index]
            reset_vibe_conversation(vibe, user)
        except ValueError:
            logger.error(f"Invalid input: {vibe_index}")
            return

def reset_vibe_conversation(vibe, user):
    """Reset the conversation history for a vibe."""
    logger.info(f"Resetting conversation history for vibe '{vibe.title}' (slug: {vibe.slug})")
    
    # Get the conversation history
    try:
        conversation_history = VibeConversationHistory.objects.get(vibe=vibe, user=user)
        
        # Print the current conversation history
        logger.info(f"Current conversation history has {len(conversation_history.conversation)} messages")
        
        # Reset the conversation history
        conversation_history.conversation = []
        conversation_history.message_count = 0
        conversation_history.save()
        
        logger.info(f"Conversation history reset for vibe '{vibe.title}'")
    except VibeConversationHistory.DoesNotExist:
        logger.info(f"No conversation history found for vibe '{vibe.title}'. Creating a new one.")
        
        # Create a new conversation history
        conversation_history = VibeConversationHistory.objects.create(
            vibe=vibe,
            user=user,
            conversation=[]
        )
        
        logger.info(f"New conversation history created for vibe '{vibe.title}'")

if __name__ == "__main__":
    main()
