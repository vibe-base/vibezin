"""
Utility functions for AI image generation using DALL-E.
"""
import os
import json
import logging
import requests
from io import BytesIO
from typing import Dict, Any, Tuple, Optional
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import uuid

from .utils import upload_to_ipfs

logger = logging.getLogger(__name__)

# OpenAI API endpoints
OPENAI_API_URL = "https://api.openai.com/v1"
DALLE_ENDPOINT = f"{OPENAI_API_URL}/images/generations"

def generate_image(
    api_key: str, 
    prompt: str, 
    size: str = "1024x1024", 
    quality: str = "standard", 
    model: str = "dall-e-3"
) -> Dict[str, Any]:
    """
    Generate an image using DALL-E.
    
    Args:
        api_key: OpenAI API key
        prompt: The image description
        size: Image size (1024x1024, 1024x1792, or 1792x1024)
        quality: Image quality (standard or hd)
        model: DALL-E model version
        
    Returns:
        Dictionary with the result of the operation
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality
        }
        
        logger.info(f"Sending request to DALL-E API with prompt: {prompt[:50]}...")
        
        response = requests.post(
            DALLE_ENDPOINT,
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully generated image with DALL-E")
            return {
                "success": True,
                "data": result,
                "image_url": result["data"][0]["url"],
                "revised_prompt": result["data"][0].get("revised_prompt", prompt)
            }
        else:
            logger.error(f"DALL-E API error: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"DALL-E API error: {response.status_code}",
                "details": response.text
            }
    except Exception as e:
        logger.exception(f"Error generating image: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to generate image: {str(e)}"
        }

def download_image(image_url: str) -> Optional[BytesIO]:
    """
    Download an image from a URL.
    
    Args:
        image_url: URL of the image
        
    Returns:
        BytesIO object containing the image data or None if download failed
    """
    try:
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            return image_data
        else:
            logger.error(f"Failed to download image: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.exception(f"Error downloading image: {str(e)}")
        return None

def save_generated_image(user: User, prompt: str, image_url: str, revised_prompt: str = None) -> Dict[str, Any]:
    """
    Download a generated image and save it to IPFS.
    
    Args:
        user: The user who generated the image
        prompt: The original prompt
        image_url: URL of the generated image
        revised_prompt: The revised prompt used by DALL-E (if any)
        
    Returns:
        Dictionary with the result of the operation
    """
    try:
        # Download the image
        image_data = download_image(image_url)
        if not image_data:
            return {
                "success": False,
                "error": "Failed to download the generated image"
            }
        
        # Generate a unique filename
        filename = f"dalle_{uuid.uuid4()}.png"
        
        # Upload to IPFS
        success, result = upload_to_ipfs(image_data, filename)
        
        if success:
            # Create a record in the database
            from .models import GeneratedImage
            image = GeneratedImage.objects.create(
                user=user,
                prompt=prompt,
                revised_prompt=revised_prompt or prompt,
                image_url=result
            )
            
            return {
                "success": True,
                "image_url": result,
                "image_id": image.id,
                "message": "Image saved successfully"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to upload image to IPFS: {result}"
            }
    except Exception as e:
        logger.exception(f"Error saving generated image: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to save generated image: {str(e)}"
        }
