#!/usr/bin/env python
"""
Create a test conversation history with a write_file tool call.
"""
import os
import sys
import django
import logging
import json
from pathlib import Path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Create a test conversation history with a write_file tool call."""
    from vibezin.models import Vibe, User, VibeConversationHistory
    from vibezin.file_utils import VibeFileManager
    
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
        
        # Create a file manager
        file_manager = VibeFileManager(vibe)
        
        # Get the vibe directory
        vibe_dir = file_manager.vibe_dir
        logger.info(f"Vibe directory: {vibe_dir}")
        
        # Check if the directory exists
        if not vibe_dir.exists():
            logger.info(f"Creating vibe directory: {vibe_dir}")
            vibe_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test conversation history
        conversation_history, created = VibeConversationHistory.objects.get_or_create(
            vibe=vibe,
            user=user,
            defaults={
                'conversation': []
            }
        )
        
        logger.info(f"{'Created' if created else 'Using existing'} conversation history: {conversation_history.id}")
        
        # Create a test message with a write_file tool call
        test_message = """
I'll help you create a page about dogs with an image. Let me first check if there are any existing files:

```tool
list_files
```

Tool result:
Files in the vibe directory:
- content.json (102 bytes)
- dog-styles.css (586 bytes)
- dog.jpg (38153 bytes)
- dogs.html (543 bytes)
- index.html (1705 bytes)
- index.html.bak (271 bytes)
- metadata.json (266 bytes)
- simulate_ai.html (271 bytes)
- simulate_ai.html.bak (241 bytes)
- style.css (454 bytes)
- test_dalle.html (950 bytes)
- test_dog.png (38153 bytes)
- test_dog.png.html (38153 bytes)

Now, let me check if there are any images available:

```tool
list_images
```

Tool result:
## Images in the vibe directory:
- **dog.jpg** <img src="/static/vibes/test-user-vibe/dog.jpg" alt="dog.jpg" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
  - Size: 38153 bytes
  - Path: /static/vibes/test-user-vibe/dog.jpg
  - HTML: `<img src="/static/vibes/test-user-vibe/dog.jpg" alt="dog.jpg" class="vibe-image">`
  - HTML with link: `<a href="https://example.com" target="_blank"><img src="/static/vibes/test-user-vibe/dog.jpg" alt="dog.jpg" class="vibe-image"></a>`

- **test_dog.png** <img src="/static/vibes/test-user-vibe/test_dog.png" alt="test_dog.png" style="max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
  - Size: 38153 bytes
  - Path: /static/vibes/test-user-vibe/test_dog.png
  - HTML: `<img src="/static/vibes/test-user-vibe/test_dog.png" alt="test_dog.png" class="vibe-image">`
  - HTML with link: `<a href="https://example.com" target="_blank"><img src="/static/vibes/test-user-vibe/test_dog.png" alt="test_dog.png" class="vibe-image"></a>`

## How to use these images:
1. Copy the HTML code for the image you want to use
2. Paste it into your HTML file using the write_file tool
3. You can modify the HTML to change the size, add classes, or make the image a link
4. Example of making an image link to another page: `<a href="another-page.html"><img src="IMAGE_URL" alt="Description"></a>`

Great! I'll now update the index.html file to include the dog image:

```tool
write_file
filename: index.html
content:
<!DOCTYPE html>
<html>
<head>
    <title>My Love for Dogs</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>My Love for Dogs</h1>
    
    <h2>Why I Love Dogs</h2>
    <p>Dogs are not just pets; they are members of our families. Their unwavering loyalty and endless joy bring light to our lives every day.</p>
    
    <img src="/static/vibes/test-user-vibe/dog.jpg" alt="A cute dog" class="vibe-image">
    
    <p>Dogs provide unconditional love and companionship that enriches our lives in countless ways. From their excited greetings when we come home to their comforting presence during difficult times, dogs truly are our best friends.</p>
    
    <h2>The Joy of Dog Ownership</h2>
    <p>Owning a dog comes with many responsibilities, but the rewards far outweigh the challenges. Daily walks, playtime, and training sessions create a special bond that continues to grow stronger over time.</p>
    
    <p>Whether we're hiking in the mountains, relaxing at home, or simply enjoying each other's company, dogs bring happiness and meaning to every moment we share.</p>
</body>
</html>
```

I've updated the index.html file with a beautiful page about dogs, including the dog image from your vibe directory. The image is displayed using the correct path: `/static/vibes/test-user-vibe/dog.jpg`.

You can view the page by clicking "Refresh" in the preview panel. If you'd like to make any changes or add more content, just let me know!
"""
        
        # Add the test message to the conversation history
        conversation_history.add_message('user', 'Create a page about dogs with an image')
        conversation_history.add_message('assistant', test_message)
        conversation_history.save()
        
        logger.info("Added test message to conversation history")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
