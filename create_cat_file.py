#!/usr/bin/env python
"""
Script to create a cat.html file in all vibes.
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

from django.conf import settings
from vibezin.models import Vibe
from vibezin.file_utils import VibeFileManager

def main():
    """Create a cat.html file in all vibes."""
    # Get all vibes
    vibes = Vibe.objects.all()
    if not vibes:
        logger.error("No vibes found.")
        return
    
    logger.info(f"Found {len(vibes)} vibes")
    
    # Create cat.html in each vibe
    for vibe in vibes:
        logger.info(f"Creating cat.html in vibe: {vibe.title} (slug: {vibe.slug})")
        
        # Create the file manager
        file_manager = VibeFileManager(vibe)
        
        # Check if the vibe directory exists
        vibe_dir = file_manager.vibe_dir
        logger.info(f"Vibe directory: {vibe_dir}")
        logger.info(f"Vibe directory exists: {vibe_dir.exists()}")
        
        # Ensure the vibe directory exists
        if not vibe_dir.exists():
            logger.info(f"Creating vibe directory: {vibe_dir}")
            vibe_dir.mkdir(parents=True, exist_ok=True)
        
        # Create the cat.html file
        cat_html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Cats - The Internet's Favorite</title>
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
            color: #ff6b6b;
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
        .cat-facts {
            background-color: #f0f0f0;
            padding: 20px;
            border-radius: 10px;
            margin-top: 30px;
        }
        .cat-facts h2 {
            color: #ff6b6b;
            margin-top: 0;
        }
        .cat-facts ul {
            padding-left: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Cats - The Internet's Favorite</h1>
        
        <p>Cats have been internet celebrities since the dawn of social media. Their cute faces, playful antics, and sometimes grumpy expressions have captured the hearts of millions around the world.</p>
        
        <img src="https://placekitten.com/800/500" alt="A cute cat">
        
        <p>From Grumpy Cat to Maru, feline internet stars have amassed followers, book deals, and even movie appearances. What is it about cats that makes them so irresistible online?</p>
        
        <p>Perhaps it's their independent nature, their unpredictable behavior, or simply their adorable faces. Whatever the reason, cats continue to rule the internet kingdom.</p>
        
        <div class="cat-facts">
            <h2>Fun Cat Facts</h2>
            <ul>
                <li>Cats spend about 70% of their lives sleeping</li>
                <li>A group of cats is called a "clowder"</li>
                <li>Cats have 32 muscles in each ear</li>
                <li>A cat's purr vibrates at a frequency that promotes tissue healing</li>
                <li>Cats can rotate their ears 180 degrees</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""
        
        # Try to write the file directly
        cat_html_path = vibe_dir / "cat.html"
        logger.info(f"Writing cat.html directly to: {cat_html_path}")
        
        try:
            with open(cat_html_path, 'w') as f:
                f.write(cat_html_content)
            
            # Check if the file was created
            if cat_html_path.exists():
                logger.info(f"Successfully created cat.html: {cat_html_path}")
                logger.info(f"File size: {cat_html_path.stat().st_size} bytes")
            else:
                logger.error(f"Failed to create cat.html: {cat_html_path}")
        except Exception as e:
            logger.exception(f"Error creating cat.html: {str(e)}")
        
        # Also try using the file manager
        logger.info(f"Writing cat.html using file manager")
        result = file_manager.write_file("cat.html", cat_html_content)
        logger.info(f"File manager result: {result}")

if __name__ == "__main__":
    main()
