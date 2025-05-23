"""
Utilities for processing HTML content.
"""
import re
import logging
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

def sanitize_image_urls(html_content: str, vibe_slug: str) -> str:
    """
    Sanitize image URLs in HTML content to ensure they use absolute Pinata IPFS URLs.
    
    Args:
        html_content: The HTML content to sanitize
        vibe_slug: The slug of the vibe
        
    Returns:
        The sanitized HTML content
    """
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all img tags
        img_tags = soup.find_all('img')
        logger.info(f"Found {len(img_tags)} img tags in HTML content")
        
        # Process each img tag
        for img in img_tags:
            src = img.get('src')
            if not src:
                logger.warning("Found img tag without src attribute")
                continue
                
            logger.info(f"Processing img tag with src: {src}")
            
            # Check if the src is already an absolute URL
            if src.startswith(('http://', 'https://')):
                # Check if it's a Pinata IPFS URL
                if 'ipfs.io/ipfs/' in src or 'gateway.pinata.cloud/ipfs/' in src:
                    logger.info(f"Image already uses Pinata IPFS URL: {src}")
                    continue
                else:
                    logger.warning(f"Image uses non-Pinata URL: {src}")
                    # We'll keep non-Pinata absolute URLs as they might be external resources
                    continue
            
            # Handle relative paths
            if src.startswith('/'):
                # Absolute path within the site
                logger.warning(f"Image uses absolute path within site: {src}")
                # Check if it's a path to a vibe image
                if f'/static/vibes/{vibe_slug}/' in src:
                    # This is a vibe image, but we don't have the Pinata URL
                    # We'll keep it as is for now
                    logger.warning(f"Image uses vibe path but not Pinata URL: {src}")
                    continue
            else:
                # Relative path within the vibe
                logger.warning(f"Image uses relative path: {src}")
                # Check if it's a simple filename
                if '/' not in src:
                    # This might be a vibe image, but we don't have the Pinata URL
                    # We'll convert it to an absolute path within the site
                    new_src = f"/static/vibes/{vibe_slug}/{src}"
                    logger.info(f"Converting relative path to absolute path: {src} -> {new_src}")
                    img['src'] = new_src
        
        # Convert the soup back to HTML
        sanitized_html = str(soup)
        logger.info(f"Sanitized HTML content: {len(sanitized_html)} bytes")
        
        return sanitized_html
    except Exception as e:
        logger.exception(f"Error sanitizing image URLs: {str(e)}")
        # Return the original content if there's an error
        return html_content

def extract_image_references(html_content: str) -> List[Dict[str, Any]]:
    """
    Extract image references from HTML content.
    
    Args:
        html_content: The HTML content to extract image references from
        
    Returns:
        A list of dictionaries with image information
    """
    try:
        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all img tags
        img_tags = soup.find_all('img')
        logger.info(f"Found {len(img_tags)} img tags in HTML content")
        
        # Extract information from each img tag
        images = []
        for img in img_tags:
            src = img.get('src')
            if not src:
                logger.warning("Found img tag without src attribute")
                continue
                
            alt = img.get('alt', '')
            
            # Check if the src is a Pinata IPFS URL
            is_pinata = False
            if src.startswith(('http://', 'https://')):
                if 'ipfs.io/ipfs/' in src or 'gateway.pinata.cloud/ipfs/' in src:
                    is_pinata = True
            
            images.append({
                'src': src,
                'alt': alt,
                'is_pinata': is_pinata
            })
        
        return images
    except Exception as e:
        logger.exception(f"Error extracting image references: {str(e)}")
        return []
