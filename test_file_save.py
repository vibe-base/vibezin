#!/usr/bin/env python
"""
Test script to directly save a file to a vibe directory.
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
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Test saving a file to a vibe directory."""
    from vibezin.models import Vibe
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
        
        # Create a file manager
        file_manager = VibeFileManager(vibe)
        
        # Get the vibe directory
        vibe_dir = file_manager.vibe_dir
        logger.info(f"Vibe directory: {vibe_dir}")
        
        # Check if the directory exists
        if not vibe_dir.exists():
            logger.info(f"Creating vibe directory: {vibe_dir}")
            vibe_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a test file
        filename = "index.html"
        file_path = file_manager.get_file_path(filename)
        logger.info(f"File path: {file_path}")
        
        # Create the file content
        content = """<!DOCTYPE html>
<html>
<head>
    <title>Test File</title>
</head>
<body>
    <h1>Test File</h1>
    <p>This is a test file created by the test script.</p>
    <img src="https://example.com/image.jpg" alt="Test Image">
</body>
</html>"""
        
        # Write the file directly
        logger.info(f"Writing file directly to: {file_path}")
        with open(file_path, 'w') as f:
            f.write(content)
        logger.info(f"File written directly: {file_path}")
        
        # Check if the file exists
        if file_path.exists():
            logger.info(f"File exists: {file_path}")
            with open(file_path, 'r') as f:
                file_content = f.read()
            logger.info(f"File content: {file_content[:100]}...")
        else:
            logger.error(f"File does not exist: {file_path}")
        
        # Now try using the file manager
        logger.info(f"Writing file using file manager: {filename}")
        result = file_manager.write_file(filename, content)
        logger.info(f"File manager result: {result}")
        
        # Check if the file exists again
        if file_path.exists():
            logger.info(f"File exists after using file manager: {file_path}")
            with open(file_path, 'r') as f:
                file_content = f.read()
            logger.info(f"File content after using file manager: {file_content[:100]}...")
        else:
            logger.error(f"File does not exist after using file manager: {file_path}")
        
        # List all files in the vibe directory
        logger.info(f"Listing files in vibe directory: {vibe_dir}")
        for file in vibe_dir.iterdir():
            logger.info(f"File: {file}")
        
        # List all files using the file manager
        logger.info(f"Listing files using file manager")
        files = file_manager.list_files()
        logger.info(f"Files: {files}")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
