#!/usr/bin/env python
"""
Script to test creating a rabbit.html file directly.
"""
import os
import sys
import django
import logging
from pathlib import Path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from django.contrib.auth.models import User
from vibezin.models import Vibe
from vibezin.file_utils import VibeFileManager
from vibezin.ai_tools import process_tool_calls, handle_write_file

def main():
    """Test creating a rabbit.html file directly."""
    # Get the first user
    user = User.objects.first()
    if not user:
        logger.error("No users found.")
        return
    
    logger.info(f"Using user: {user.username}")
    
    # Get the first vibe
    vibe = Vibe.objects.first()
    if not vibe:
        logger.error("No vibes found.")
        return
    
    logger.info(f"Using vibe: {vibe.title} (slug: {vibe.slug})")
    
    # Create a file manager
    file_manager = VibeFileManager(vibe)
    
    # Test the write_file tool directly
    logger.info("Testing write_file tool directly")
    
    # Create a rabbit.html file
    rabbit_html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Rabbits - Fluffy and Adorable</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f9f9f9;
            color: #333;
        }
        h1 {
            color: #8e44ad;
            text-align: center;
            margin-bottom: 30px;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            border-radius: 10px;
        }
        p {
            margin-bottom: 20px;
        }
        .rabbit-facts {
            background-color: #f0f0f0;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .rabbit-facts h2 {
            color: #8e44ad;
            margin-top: 0;
        }
        .rabbit-facts ul {
            padding-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Rabbits - Fluffy and Adorable</h1>
        
        <p>Rabbits are small mammals known for their fluffy tails, long ears, and strong hind legs. They are popular pets and are loved for their cute appearance and gentle nature.</p>
        
        <img src="https://source.unsplash.com/random/800x500/?rabbit" alt="A cute rabbit">
        
        <p>Domesticated rabbits come in many breeds, sizes, and colors. From the tiny Netherland Dwarf to the giant Flemish Giant, there's a rabbit breed for everyone!</p>
        
        <p>Rabbits are social animals that enjoy companionship, whether from humans or other rabbits. They communicate through a variety of behaviors, including thumping their hind legs when alarmed.</p>
        
        <div class="rabbit-facts">
            <h2>Fun Rabbit Facts</h2>
            <ul>
                <li>A rabbit's teeth never stop growing throughout its life</li>
                <li>Rabbits can see almost 360 degrees around them</li>
                <li>A happy rabbit will sometimes jump and twist in the air, a behavior called a "binky"</li>
                <li>Rabbits are crepuscular, meaning they are most active at dawn and dusk</li>
                <li>A group of rabbits is called a "colony" or a "herd"</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
    
    # Create the tool call lines
    tool_call_lines = [
        "write_file",
        "filename: rabbit.html",
        "content:",
    ] + rabbit_html_content.split("\n")
    
    # Call the handle_write_file function directly
    logger.info("Calling handle_write_file directly")
    result = handle_write_file(file_manager, tool_call_lines)
    logger.info(f"Result: {result}")
    
    # Check if the file was created
    rabbit_html_path = file_manager.get_file_path("rabbit.html")
    if rabbit_html_path.exists():
        logger.info(f"rabbit.html exists: {rabbit_html_path}")
        logger.info(f"File size: {rabbit_html_path.stat().st_size} bytes")
    else:
        logger.error(f"rabbit.html does not exist: {rabbit_html_path}")
    
    # Test the process_tool_calls function
    logger.info("Testing process_tool_calls function")
    
    # Create a tool call in the format expected by process_tool_calls
    tool_call = f"""
I'll create a rabbit.html file for you!

```tool
write_file
filename: rabbit.html
content:
{rabbit_html_content}
```

Now I've created a beautiful rabbit.html file for you!
"""
    
    # Call the process_tool_calls function
    logger.info("Calling process_tool_calls")
    processed_content = process_tool_calls(tool_call, vibe, user)
    logger.info(f"Processed content length: {len(processed_content)}")
    
    # Check if the file was created again
    if rabbit_html_path.exists():
        logger.info(f"rabbit.html exists after process_tool_calls: {rabbit_html_path}")
        logger.info(f"File size: {rabbit_html_path.stat().st_size} bytes")
    else:
        logger.error(f"rabbit.html does not exist after process_tool_calls: {rabbit_html_path}")

if __name__ == "__main__":
    main()
