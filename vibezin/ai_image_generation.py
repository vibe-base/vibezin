"""
Image generation utilities for AI assistants.
"""
import logging
import requests
from typing import Dict, Any
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

# OpenAI API endpoints
OPENAI_API_URL = "https://api.openai.com/v1"
IMAGE_GENERATION_ENDPOINT = f"{OPENAI_API_URL}/images/generations"

def generate_image(api_key: str, prompt: str, size: str = "1024x1024", quality: str = "standard") -> Dict[str, Any]:
    """
    Generate an image using DALL-E.

    Args:
        api_key: OpenAI API key
        prompt: The prompt to generate an image from
        size: The size of the image (1024x1024, 512x512, or 256x256)
        quality: The quality of the image (standard or hd)

    Returns:
        A dictionary with the result of the image generation
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "url"
        }

        response = requests.post(
            IMAGE_GENERATION_ENDPOINT,
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "image_url": data["data"][0]["url"],
                "revised_prompt": data["data"][0].get("revised_prompt", prompt)
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


def save_generated_image(user: User, prompt: str, image_url: str, revised_prompt: str = None) -> Dict[str, Any]:
    """
    Save a generated image to IPFS and the database.

    Args:
        user: The user who generated the image
        prompt: The prompt used to generate the image
        image_url: The URL of the generated image
        revised_prompt: The revised prompt used by DALL-E (if any)

    Returns:
        A dictionary with the result of saving the image
    """
    try:
        # Download the image
        response = requests.get(image_url)
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"Failed to download image: HTTP {response.status_code}"
            }

        # Upload to IPFS using Pinata
        from .pinata_utils import upload_to_pinata
        pinata_result = upload_to_pinata(response.content)

        if not pinata_result.get('success', False):
            return {
                "success": False,
                "error": f"Failed to upload to IPFS: {pinata_result.get('error', 'Unknown error')}"
            }

        # Save to database
        from .models import GeneratedImage
        image = GeneratedImage.objects.create(
            user=user,
            prompt=prompt,
            revised_prompt=revised_prompt or prompt,
            ipfs_hash=pinata_result.get('ipfs_hash'),
            ipfs_url=pinata_result.get('ipfs_url')
        )

        return {
            "success": True,
            "image_id": image.id,
            "image_url": pinata_result.get('ipfs_url')
        }

    except Exception as e:
        logger.exception(f"Error saving generated image: {str(e)}")
        return {
            "success": False,
            "error": f"Failed to save generated image: {str(e)}"
        }
