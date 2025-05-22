#!/usr/bin/env python
"""
Script to set the ChatGPT API key for a user.
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
from vibezin.models import UserProfile

def main():
    """Set the ChatGPT API key for a user."""
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
        
        # Create a profile for the user
        logger.info(f"Creating profile for user '{user.username}'")
        profile = UserProfile.objects.create(user=user)
    else:
        profile = user.profile
    
    # Get the current API key
    current_key = profile.chatgpt_api_key
    if current_key:
        logger.info(f"Current API key: {current_key[:5]}...")
    else:
        logger.info("No API key set.")
    
    # Ask for a new API key
    new_key = input("Enter a new API key (or press Enter to keep the current key): ")
    
    if new_key:
        profile.chatgpt_api_key = new_key
        profile.save()
        logger.info(f"API key updated for user '{user.username}'.")
    else:
        logger.info("API key not changed.")

if __name__ == "__main__":
    main()
