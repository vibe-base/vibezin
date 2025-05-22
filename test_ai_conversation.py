#!/usr/bin/env python
"""
Test script to simulate an AI conversation.
"""
import os
import sys
import django
import logging

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Simulate an AI conversation."""
    from vibezin.models import Vibe, User
    from vibezin.ai_conversation import VibeConversation
    from vibezin.ai_tools import process_tool_calls
    
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
        
        # Create a simulated AI response with a tool call
        ai_response = """I'll create an index.html file with a simple structure that includes an image.

```tool
write_file
filename: index.html
content:
<!DOCTYPE html>
<html>
<head>
    <title>Test Page</title>
</head>
<body>
    <h1>Test Page</h1>
    <p>This is a test page created by the AI conversation.</p>
    <img src="https://example.com/image.jpg" alt="Test Image">
</body>
</html>
```

Now let's check if the file was created:

```tool
list_files
```
"""
        
        # Process the tool calls
        logger.info("Processing tool calls...")
        processed_content = process_tool_calls(ai_response, vibe, user)
        logger.info(f"Processed content: {processed_content}")
        
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
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
