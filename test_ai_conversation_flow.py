#!/usr/bin/env python
"""
Test script to verify AI conversation flow.
"""
import os
import sys
import json
import logging
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

from django.contrib.auth.models import User
from vibezin.models import Vibe, VibeConversationHistory
from vibezin.ai_conversation import VibeConversation
from vibezin.ai_tools import process_tool_calls

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test AI conversation flow."""
    # Get the vibe slug from command line arguments
    if len(sys.argv) > 1:
        vibe_slug = sys.argv[1]
    else:
        vibe_slug = "test-vibe"  # Default vibe slug
    
    logger.info(f"Testing AI conversation flow for vibe: {vibe_slug}")
    
    try:
        # Get the vibe
        vibe = Vibe.objects.get(slug=vibe_slug)
        logger.info(f"Found vibe: {vibe.title} (slug: {vibe.slug})")
        
        # Get the user
        user = vibe.user
        logger.info(f"Vibe owner: {user.username}")
        
        # Reset conversation history
        logger.info("Resetting conversation history...")
        conversation_history, created = VibeConversationHistory.objects.get_or_create(
            vibe=vibe,
            user=user,
            defaults={
                'conversation': []
            }
        )
        conversation_history.conversation = []
        conversation_history.message_count = 0
        conversation_history.save()
        logger.info("Conversation history reset")
        
        # Add a user message
        user_message = "Please update the index.html file to include information about my cat."
        logger.info(f"Adding user message: {user_message}")
        conversation_history.add_message('user', user_message)
        
        # Create a simulated AI response with a tool call
        ai_response = """I'll help you update the index.html file to include information about your cat. First, let me check the current content of the file.

```tool
read_file
filename: index.html
```

Now I'll update the file with information about your cat:

```tool
write_file
filename: index.html
content:
<!DOCTYPE html>
<html>
<head>
    <title>Updated Page with Cat Info</title>
</head>
<body>
    <h1>Updated Page with Cat Info</h1>
    <p>This page was updated by the AI assistant.</p>
    <div class="cat-info">
        <h2>About My Cat</h2>
        <p>My cat is a fluffy orange tabby named Whiskers. She loves to play with yarn and sleep in sunny spots.</p>
    </div>
</body>
</html>
```

I've updated the index.html file to include information about your cat. The file now has a section with a heading "About My Cat" and a paragraph describing your fluffy orange tabby named Whiskers.
"""
        
        # Add the AI response to the conversation history
        logger.info("Adding AI response to conversation history")
        conversation_history.add_message('assistant', ai_response)
        
        # Process the tool calls in the AI response
        logger.info("Processing tool calls in AI response")
        processed_content = process_tool_calls(ai_response, vibe, user)
        logger.info(f"Processed content length: {len(processed_content)}")
        
        # Check if the file was updated
        from vibezin.file_utils import VibeFileManager
        file_manager = VibeFileManager(vibe)
        file_path = file_manager.get_file_path("index.html")
        
        if file_path.exists():
            logger.info(f"File exists: {file_path}")
            with open(file_path, 'r') as f:
                file_content = f.read()
            logger.info(f"File content length: {len(file_content)}")
            logger.info(f"File content preview: {file_content[:100]}...")
            
            # Check if the file contains information about the cat
            if "About My Cat" in file_content and "Whiskers" in file_content:
                logger.info("SUCCESS: File was updated with cat information")
            else:
                logger.error("FAILURE: File does not contain cat information")
        else:
            logger.error(f"FAILURE: File does not exist: {file_path}")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
