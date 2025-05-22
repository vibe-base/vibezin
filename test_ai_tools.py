#!/usr/bin/env python
"""
Test script to test the AI tools.
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
    from vibezin.models import Vibe
    from vibezin.file_utils import VibeFileManager
    from vibezin.ai_tools import handle_write_file, handle_list_files, handle_read_file
    
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
        
        # Create a test file using the handle_write_file function
        logger.info("Creating test file using handle_write_file...")
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
            "filename: index.html",
            "content:",
            test_content
        ]
        
        logger.info("Calling handle_write_file...")
        result = handle_write_file(file_manager, lines)
        logger.info(f"Result: {result}")
        
        # Check if the file exists
        file_path = file_manager.get_file_path("index.html")
        if file_path.exists():
            logger.info(f"File exists: {file_path}")
            with open(file_path, 'r') as f:
                file_content = f.read()
            logger.info(f"File content: {file_content[:100]}...")
        else:
            logger.error(f"File does not exist: {file_path}")
        
        # List files again
        logger.info("Listing files again...")
        files_result = handle_list_files(file_manager)
        logger.info(f"Files result: {files_result}")
        
        # Read the file
        logger.info("Reading file...")
        read_result = handle_read_file(file_manager, ["read_file", "filename: index.html"])
        logger.info(f"Read result: {read_result}")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
