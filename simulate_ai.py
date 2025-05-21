#!/usr/bin/env python
"""
Script to simulate what the AI is doing when it saves a file.
"""
import os
import django
import logging
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Simulate what the AI is doing when it saves a file."""
    from vibezin.models import Vibe
    from vibezin.file_utils import VibeFileManager
    from vibezin.ai_tools import handle_write_file, handle_list_files, handle_read_file
    
    # Get the vibe slug from command line arguments
    if len(sys.argv) > 1:
        vibe_slug = sys.argv[1]
    else:
        vibe_slug = 'test-user-vibe'  # Default to test-user-vibe
    
    try:
        # Get the vibe
        vibe = Vibe.objects.get(slug=vibe_slug)
        logger.info(f"Using vibe: {vibe.title} (slug: {vibe.slug})")
        
        # Create a file manager
        file_manager = VibeFileManager(vibe)
        
        # List files
        logger.info("Listing files...")
        files_result = handle_list_files(file_manager)
        logger.info(f"Files result: {files_result}")
        
        # Read index.html if it exists
        logger.info("Reading index.html...")
        read_result = handle_read_file(file_manager, ["read_file", "filename: index.html"])
        logger.info(f"Read result: {read_result}")
        
        # Create a test file
        logger.info("Creating test file...")
        test_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test File</title>
</head>
<body>
    <h1>Test File</h1>
    <p>This is a test file created by the simulate_ai script.</p>
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
        
        # Check if the file was created
        file_path = os.path.join("static", "vibes", vibe.slug, "simulate_ai.html")
        if os.path.exists(file_path):
            logger.info(f"File created successfully at: {file_path}")
            with open(file_path, "r") as f:
                content = f.read()
            logger.info(f"File content (first 100 chars): {content[:100]}...")
        else:
            logger.error(f"File not created at: {file_path}")
    
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
