#!/usr/bin/env python
"""
Test script to verify file writing functionality.
"""
import os
import sys
import logging
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

from vibezin.models import Vibe
from vibezin.file_utils import VibeFileManager
from vibezin.ai_tools import handle_write_file

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main function to test file writing."""
    # Get the vibe slug from command line arguments
    if len(sys.argv) > 1:
        vibe_slug = sys.argv[1]
    else:
        vibe_slug = "test-vibe"  # Default vibe slug

    logger.info(f"Testing file writing for vibe: {vibe_slug}")

    try:
        # Get the vibe
        vibe = Vibe.objects.get(slug=vibe_slug)
        logger.info(f"Found vibe: {vibe.title} (slug: {vibe.slug})")

        # Create a file manager
        file_manager = VibeFileManager(vibe)
        logger.info(f"Created file manager for vibe: {vibe.slug}")

        # Check if the vibe directory exists
        logger.info(f"Vibe directory: {file_manager.vibe_dir}")
        logger.info(f"Vibe directory exists: {file_manager.vibe_dir.exists()}")

        # List existing files
        files = file_manager.list_files()
        logger.info(f"Found {len(files)} files in vibe directory:")
        for file in files:
            logger.info(f"- {file['name']} ({file['size']} bytes)")

        # Test updating an existing file
        if any(file['name'] == 'index.html' for file in files):
            logger.info("Found index.html, updating it...")

            # Read the current content
            result = file_manager.read_file('index.html')
            if result['success']:
                current_content = result['content']
                logger.info(f"Current content length: {len(current_content)}")
                logger.info(f"Current content preview: {current_content[:100]}...")

                # Create updated content
                updated_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Updated Test Page</title>
</head>
<body>
    <h1>Updated Test Page</h1>
    <p>This page was updated by the test_update_file.py script.</p>
    <p>Original content length: {len(current_content)} bytes</p>
    <p>Updated at: {django.utils.timezone.now()}</p>
    <p>Information about my cat: She is a fluffy orange tabby named Whiskers!</p>
</body>
</html>"""

                # Update the file using the file manager directly
                logger.info("Updating file using file_manager.write_file...")
                result = file_manager.write_file('index.html', updated_content)
                logger.info(f"Result: {result}")

                # Verify the file was updated
                file_path = file_manager.get_file_path('index.html')
                if file_path.exists():
                    logger.info(f"File exists after update: {file_path}")
                    with open(file_path, 'r') as f:
                        new_content = f.read()
                    logger.info(f"New content length: {len(new_content)}")
                    logger.info(f"New content preview: {new_content[:100]}...")
                else:
                    logger.error(f"File does not exist after update: {file_path}")
            else:
                logger.error(f"Error reading index.html: {result.get('error')}")
        else:
            logger.info("index.html not found, creating it...")

            # Create a new index.html file
            new_content = """<!DOCTYPE html>
<html>
<head>
    <title>New Test Page</title>
</head>
<body>
    <h1>New Test Page</h1>
    <p>This page was created by the test_update_file.py script.</p>
    <p>Created at: {django.utils.timezone.now()}</p>
</body>
</html>"""

            # Create the file using the file manager
            logger.info("Creating file using file_manager.write_file...")
            result = file_manager.write_file('index.html', new_content)
            logger.info(f"Result: {result}")

            # Verify the file was created
            file_path = file_manager.get_file_path('index.html')
            if file_path.exists():
                logger.info(f"File exists after creation: {file_path}")
                with open(file_path, 'r') as f:
                    content = f.read()
                logger.info(f"Content length: {len(content)}")
                logger.info(f"Content preview: {content[:100]}...")
            else:
                logger.error(f"File does not exist after creation: {file_path}")

        # Test using handle_write_file function
        logger.info("Testing handle_write_file function...")

        # Create tool call lines
        tool_call_lines = [
            "write_file",
            "filename: index.html",
            "content:",
            """<!DOCTYPE html>
<html>
<head>
    <title>Updated via Tool Call</title>
</head>
<body>
    <h1>Updated via Tool Call</h1>
    <p>This page was updated using the handle_write_file function.</p>
    <p>Updated at: {django.utils.timezone.now()}</p>
    <p>Information about my cat: She is a fluffy orange tabby named Whiskers who loves to play with yarn!</p>
</body>
</html>"""
        ]

        # Call handle_write_file
        logger.info("Calling handle_write_file...")
        result = handle_write_file(file_manager, tool_call_lines)
        logger.info(f"Result: {result}")

        # Verify the file was updated
        file_path = file_manager.get_file_path('index.html')
        if file_path.exists():
            logger.info(f"File exists after tool call update: {file_path}")
            with open(file_path, 'r') as f:
                content = f.read()
            logger.info(f"Content length: {len(content)}")
            logger.info(f"Content preview: {content[:100]}...")
        else:
            logger.error(f"File does not exist after tool call update: {file_path}")

    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
