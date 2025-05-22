#!/usr/bin/env python
"""
Test script to simulate a real AI conversation through the API.
"""
import os
import sys
import django
import logging
import requests
import json

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Simulate a real AI conversation through the API."""
    from vibezin.models import Vibe, User
    from django.contrib.auth.models import User
    from django.test import Client
    from django.urls import reverse
    
    # Get the vibe slug from command line arguments
    if len(sys.argv) > 1:
        vibe_slug = sys.argv[1]
    else:
        # Get the first vibe
        vibe = Vibe.objects.first()
        if vibe:
            vibe_slug = vibe.slug
        else:
            logger.error("No vibes found in the database.")
            return
    
    try:
        # Get the vibe
        vibe = Vibe.objects.get(slug=vibe_slug)
        logger.info(f"Using vibe: {vibe.title} (slug: {vibe.slug})")
        
        # Get the user
        user = vibe.user
        if not user:
            logger.error("Vibe has no user.")
            return
        
        logger.info(f"Using user: {user.username}")
        
        # Create a test client
        client = Client()
        
        # Log in the user
        client.force_login(user)
        
        # Send a message to the AI
        message = "Create a simple HTML page with an image"
        
        # Get the URL for the AI message endpoint
        url = reverse('vibezin:vibe_ai_message', kwargs={'vibe_slug': vibe_slug})
        logger.info(f"Sending message to URL: {url}")
        
        # Send the message
        response = client.post(url, {'message': message})
        
        # Check the response
        if response.status_code == 200:
            logger.info("Response received successfully")
            response_data = json.loads(response.content)
            logger.info(f"Response data: {response_data}")
            
            # Check if the file exists
            from vibezin.file_utils import VibeFileManager
            file_manager = VibeFileManager(vibe)
            file_path = file_manager.get_file_path("index.html")
            
            if file_path.exists():
                logger.info(f"File exists: {file_path}")
                with open(file_path, 'r') as f:
                    file_content = f.read()
                logger.info(f"File content: {file_content[:100]}...")
            else:
                logger.error(f"File does not exist: {file_path}")
        else:
            logger.error(f"Error sending message: {response.status_code}")
            logger.error(f"Response content: {response.content}")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
