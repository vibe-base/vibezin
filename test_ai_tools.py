#!/usr/bin/env python
"""
Test script to debug the AI tools.
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
    """Test the AI tools."""
    from vibezin.models import Vibe, User
    from vibezin.file_utils import VibeFileManager
    from vibezin.ai_tools import process_tool_calls, handle_write_file, handle_list_files, handle_read_file

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

        # List files
        logger.info("Listing files...")
        files_result = handle_list_files(file_manager)
        logger.info(f"Files result: {files_result}")

        # Create a test AI response with a tool call to write a file
        test_response = """
I'll help you create a page about dogs. Let me first check if there are any existing files:

```tool
list_files
```

Tool result:
Files in the vibe directory:
- content.json (102 bytes)
- dog.jpg (38153 bytes)
- index.html (1705 bytes)
- index.html.bak (271 bytes)
- metadata.json (266 bytes)
- simulate_ai.html (241 bytes)
- style.css (454 bytes)
- test_dalle.html (950 bytes)
- test_dog.png (38153 bytes)
- test_dog.png.html (38153 bytes)

Now, let me create a new HTML file about dogs:

```tool
write_file
filename: dogs.html
content:
<!DOCTYPE html>
<html>
<head>
    <title>All About Dogs</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>All About Dogs</h1>
    <p>Dogs are wonderful companions and have been living alongside humans for thousands of years.</p>
    <img src="/static/vibes/test-user-vibe/dog.jpg" alt="A cute dog">
    <h2>Popular Dog Breeds</h2>
    <ul>
        <li>Labrador Retriever</li>
        <li>German Shepherd</li>
        <li>Golden Retriever</li>
        <li>Bulldog</li>
        <li>Beagle</li>
    </ul>
</body>
</html>
```

Let me also create a new CSS file for styling:

```tool
write_file
filename: dog-styles.css
content:
body {
    font-family: Arial, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}

h1 {
    color: #333;
    text-align: center;
    border-bottom: 2px solid #4a90e2;
    padding-bottom: 10px;
}

h2 {
    color: #4a90e2;
}

img {
    max-width: 100%;
    height: auto;
    border-radius: 8px;
    margin: 20px 0;
    display: block;
    margin-left: auto;
    margin-right: auto;
}

ul {
    background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

li {
    margin-bottom: 10px;
}
```

I've created two files for you:

1. `dogs.html` - A page about dogs with some basic information and a list of popular breeds
2. `dog-styles.css` - A CSS file with styling for the page

You can view the page by clicking on "dogs.html" in the file list and then clicking "Refresh" in the preview panel.
"""

        # Process the tool calls
        logger.info("Processing tool calls...")
        processed_content = process_tool_calls(test_response, vibe, user)
        logger.info(f"Processed content: {processed_content}")

        # List all files in the vibe directory
        logger.info("Listing files in vibe directory...")
        files = file_manager.list_files()
        for file in files:
            logger.info(f"  - {file['name']} ({file['size']} bytes)")

        # Check if the dogs.html file exists
        file_path = file_manager.get_file_path("dogs.html")
        if file_path.exists():
            logger.info(f"File exists: {file_path}")
            with open(file_path, 'r') as f:
                file_content = f.read()
            logger.info(f"File content: {file_content[:100]}...")
        else:
            logger.error(f"File does not exist: {file_path}")

        # Check if the dog-styles.css file exists
        file_path = file_manager.get_file_path("dog-styles.css")
        if file_path.exists():
            logger.info(f"File exists: {file_path}")
            with open(file_path, 'r') as f:
                file_content = f.read()
            logger.info(f"File content: {file_content[:100]}...")
        else:
            logger.error(f"File does not exist: {file_path}")

        # Test direct file creation
        logger.info("Testing direct file creation...")
        test_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test File from AI Tools</title>
</head>
<body>
    <h1>Test File from AI Tools</h1>
    <p>This is a test file created by the test_ai_tools script.</p>
    <img src="https://example.com/image.jpg" alt="Test Image">
</body>
</html>"""

        # Write the file using the handle_write_file function
        lines = [
            "write_file",
            "filename: simulate_ai.html",
            "content:",
            test_content
        ]

        logger.info("Calling handle_write_file...")
        result = handle_write_file(file_manager, lines)
        logger.info(f"Result: {result}")

    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
