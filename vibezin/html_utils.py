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

    This function looks for image tags in HTML content and ensures that:
    1. DALL-E generated images use their Pinata IPFS URLs
    2. Relative paths are converted to absolute paths
    3. Any IPFS hash references are properly formatted with the full URL

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

        # Check if we need to add a warning comment
        has_relative_paths = False
        has_ipfs_hash_only = False

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
                    # Add a data attribute to indicate this is a Pinata URL
                    img['data-pinata-url'] = 'true'
                    continue
                else:
                    logger.warning(f"Image uses non-Pinata URL: {src}")
                    # We'll keep non-Pinata absolute URLs as they might be external resources
                    continue

            # Check if it's just an IPFS hash without the full URL
            if src.startswith('Qm') and len(src) >= 46 and '/' not in src:
                logger.warning(f"Image uses IPFS hash without full URL: {src}")
                # Convert to a proper IPFS URL
                new_src = f"https://gateway.pinata.cloud/ipfs/{src}"
                logger.info(f"Converting IPFS hash to full URL: {src} -> {new_src}")
                img['src'] = new_src
                img['data-original-src'] = src
                img['data-pinata-url'] = 'true'
                has_ipfs_hash_only = True
                continue

            # Handle relative paths
            if src.startswith('/'):
                # Absolute path within the site
                logger.warning(f"Image uses absolute path within site: {src}")
                # Check if it's a path to a vibe image
                if f'/static/vibes/{vibe_slug}/' in src:
                    # This is a vibe image, but we don't have the Pinata URL
                    # We'll add a warning comment and keep it as is for now
                    logger.warning(f"Image uses vibe path but not Pinata URL: {src}")
                    img['data-warning'] = 'Should use Pinata IPFS URL for reliability'
                    has_relative_paths = True
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
                    img['data-original-src'] = src
                    img['data-warning'] = 'Should use Pinata IPFS URL for reliability'
                    has_relative_paths = True

        # Add a warning comment at the top of the HTML if needed
        if has_relative_paths or has_ipfs_hash_only:
            warning = soup.new_comment("""
WARNING: Some images in this HTML are using relative paths or incomplete IPFS URLs.
For maximum reliability, all images should use complete, absolute Pinata IPFS URLs.
Example: <img src="https://gateway.pinata.cloud/ipfs/QmExample..." alt="Description">
""")
            if soup.html and soup.html.body:
                soup.html.body.insert(0, warning)
            else:
                # If there's no html or body tag, just add it at the beginning
                soup.insert(0, warning)

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
