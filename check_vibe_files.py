#!/usr/bin/env python
"""
Script to check the current vibe and its files.
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
    """Check the current vibe and its files."""
    from vibezin.models import Vibe
    from vibezin.file_utils import VibeFileManager
    
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
        
        # Create a file manager
        file_manager = VibeFileManager(vibe)
        
        # Get the vibe directory
        vibe_dir = file_manager.vibe_dir
        logger.info(f"Vibe directory: {vibe_dir}")
        
        # Check if the directory exists
        if not vibe_dir.exists():
            logger.info(f"Creating vibe directory: {vibe_dir}")
            vibe_dir.mkdir(parents=True, exist_ok=True)
        
        # List all files in the vibe directory
        logger.info(f"Files in vibe directory:")
        for file_path in vibe_dir.iterdir():
            if file_path.is_file():
                logger.info(f"  - {file_path.name} ({file_path.stat().st_size} bytes)")
                
                # If it's an HTML file, check its content
                if file_path.suffix.lower() in ['.html', '.htm']:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    logger.info(f"    Content (first 100 chars): {content[:100]}...")
                    
                    # Check for image tags
                    import re
                    img_tags = re.findall(r'<img[^>]+>', content)
                    if img_tags:
                        logger.info(f"    Found {len(img_tags)} image tags:")
                        for i, img_tag in enumerate(img_tags):
                            logger.info(f"      {i+1}. {img_tag}")
                            
                            # Extract src attribute
                            src_match = re.search(r'src=["\'](.*?)["\']', img_tag)
                            if src_match:
                                src = src_match.group(1)
                                logger.info(f"        src: {src}")
                                
                                # Check if the image exists
                                if src.startswith('/static/vibes/'):
                                    # Extract the path relative to the static directory
                                    rel_path = src[len('/static/'):]
                                    static_path = Path('static') / rel_path
                                    if static_path.exists():
                                        logger.info(f"        Image exists at: {static_path}")
                                    else:
                                        logger.warning(f"        Image does not exist at: {static_path}")
                                elif src.startswith('http'):
                                    logger.info(f"        External image URL")
                                else:
                                    # Relative path
                                    img_path = vibe_dir / src
                                    if img_path.exists():
                                        logger.info(f"        Image exists at: {img_path}")
                                    else:
                                        logger.warning(f"        Image does not exist at: {img_path}")
        
        # List all files in the static directory
        static_dir = Path('static')
        if static_dir.exists():
            logger.info(f"Files in static directory:")
            for file_path in static_dir.iterdir():
                if file_path.is_dir():
                    logger.info(f"  - {file_path.name}/ (directory)")
        
        # List all files in the static/vibes directory
        vibes_dir = static_dir / 'vibes'
        if vibes_dir.exists():
            logger.info(f"Files in static/vibes directory:")
            for file_path in vibes_dir.iterdir():
                if file_path.is_dir():
                    logger.info(f"  - {file_path.name}/ (directory)")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
