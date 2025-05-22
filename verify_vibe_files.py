#!/usr/bin/env python
"""
Verify that files are being saved correctly in the vibe directory.
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
    """Verify that files are being saved correctly in the vibe directory."""
    from vibezin.models import Vibe
    from vibezin.file_utils import VibeFileManager
    from vibezin.vibe_utils import get_vibe_directory, ensure_vibe_directory_exists
    from django.conf import settings
    
    # Get the vibe slug from command line arguments
    if len(sys.argv) > 1:
        vibe_slug = sys.argv[1]
    else:
        # Get all vibes
        vibes = Vibe.objects.all()
        if not vibes:
            logger.error("No vibes found in the database.")
            return
        
        # Print all vibes
        logger.info("Available vibes:")
        for vibe in vibes:
            logger.info(f"  - {vibe.slug}: {vibe.title}")
        
        # Use the first vibe
        vibe_slug = vibes[0].slug
    
    try:
        # Get the vibe
        vibe = Vibe.objects.get(slug=vibe_slug)
        logger.info(f"Using vibe: {vibe.title} (slug: {vibe.slug})")
        
        # Get the vibe directory
        vibe_dir = get_vibe_directory(vibe.slug)
        logger.info(f"Vibe directory: {vibe_dir}")
        
        # Check if the directory exists
        if not vibe_dir.exists():
            logger.info(f"Creating vibe directory: {vibe_dir}")
            ensure_vibe_directory_exists(vibe.slug)
        
        # Create a file manager
        file_manager = VibeFileManager(vibe)
        
        # List all files in the vibe directory
        logger.info("Files in vibe directory:")
        files = file_manager.list_files()
        for file in files:
            logger.info(f"  - {file['name']} ({file['size']} bytes)")
        
        # Check if index.html exists
        index_path = vibe_dir / "index.html"
        if index_path.exists():
            logger.info(f"index.html exists: {index_path}")
            with open(index_path, 'r') as f:
                content = f.read()
            logger.info(f"Content (first 100 chars): {content[:100]}...")
            
            # Check if the content contains an image tag
            import re
            img_tags = re.findall(r'<img[^>]+>', content)
            if img_tags:
                logger.info(f"Found {len(img_tags)} image tags:")
                for i, img_tag in enumerate(img_tags):
                    logger.info(f"  {i+1}. {img_tag}")
                    
                    # Extract src attribute
                    src_match = re.search(r'src=["\'](.*?)["\']', img_tag)
                    if src_match:
                        src = src_match.group(1)
                        logger.info(f"    src: {src}")
                        
                        # Check if the image exists
                        if src.startswith('/static/vibes/'):
                            # Extract the path relative to the static directory
                            rel_path = src[len('/static/'):]
                            static_path = Path('static') / rel_path
                            if static_path.exists():
                                logger.info(f"    Image exists at: {static_path}")
                            else:
                                logger.warning(f"    Image does not exist at: {static_path}")
                        elif src.startswith('http'):
                            logger.info(f"    External image URL")
                        else:
                            # Relative path
                            img_path = vibe_dir / src
                            if img_path.exists():
                                logger.info(f"    Image exists at: {img_path}")
                            else:
                                logger.warning(f"    Image does not exist at: {img_path}")
        else:
            logger.warning(f"index.html does not exist: {index_path}")
        
        # Create a test file
        test_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test File</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Test File</h1>
    <p>This is a test file created by the verify_vibe_files script.</p>
    <img src="/static/vibes/test-user-vibe/dog.jpg" alt="A cute dog">
</body>
</html>"""
        
        # Write the file
        logger.info("Writing test file...")
        result = file_manager.write_file("test_verify.html", test_content)
        logger.info(f"Result: {result}")
        
        # Check if the file exists
        test_path = vibe_dir / "test_verify.html"
        if test_path.exists():
            logger.info(f"test_verify.html exists: {test_path}")
            with open(test_path, 'r') as f:
                content = f.read()
            logger.info(f"Content: {content}")
        else:
            logger.warning(f"test_verify.html does not exist: {test_path}")
        
        # Check the static directory structure
        logger.info("Static directory structure:")
        static_dir = settings.STATICFILES_DIRS[0]
        logger.info(f"Static directory: {static_dir}")
        
        # Check if the static directory exists
        if static_dir.exists():
            logger.info(f"Static directory exists: {static_dir}")
            
            # Check if the vibes directory exists
            vibes_dir = static_dir / "vibes"
            if vibes_dir.exists():
                logger.info(f"Vibes directory exists: {vibes_dir}")
                
                # List all vibe directories
                logger.info("Vibe directories:")
                for vibe_dir in vibes_dir.iterdir():
                    if vibe_dir.is_dir():
                        logger.info(f"  - {vibe_dir.name}")
                        
                        # List all files in the vibe directory
                        logger.info(f"    Files in {vibe_dir.name}:")
                        for file_path in vibe_dir.iterdir():
                            if file_path.is_file():
                                logger.info(f"      - {file_path.name} ({file_path.stat().st_size} bytes)")
            else:
                logger.warning(f"Vibes directory does not exist: {vibes_dir}")
        else:
            logger.warning(f"Static directory does not exist: {static_dir}")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
