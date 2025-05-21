"""
Utility functions for managing vibe directories and content.
"""
import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from django.conf import settings
from django.contrib.auth.models import User
from .models import Vibe
from .ai_utils import generate_vibe_content

logger = logging.getLogger(__name__)

def get_vibe_directory(vibe_slug: str) -> Path:
    """
    Get the directory path for a vibe.

    Args:
        vibe_slug: The slug of the vibe

    Returns:
        Path object for the vibe directory
    """
    return settings.VIBE_CONTENT_DIR / vibe_slug


def ensure_vibe_directory_exists(vibe_slug: str) -> Path:
    """
    Ensure that the directory for a vibe exists.

    Args:
        vibe_slug: The slug of the vibe

    Returns:
        Path object for the vibe directory
    """
    vibe_dir = get_vibe_directory(vibe_slug)

    # Create the parent directory if it doesn't exist
    if not settings.VIBE_CONTENT_DIR.exists():
        settings.VIBE_CONTENT_DIR.mkdir(parents=True, exist_ok=True)

    # Create the vibe directory if it doesn't exist
    if not vibe_dir.exists():
        vibe_dir.mkdir(parents=True, exist_ok=True)

    return vibe_dir


def create_vibe_directory(vibe: Vibe) -> Dict[str, Any]:
    """
    Create a directory for a vibe and initialize it with default files.

    Args:
        vibe: The Vibe object

    Returns:
        Dictionary with status and message
    """
    try:
        if not vibe.slug:
            return {"success": False, "message": "Vibe has no slug"}

        vibe_dir = ensure_vibe_directory_exists(vibe.slug)

        # Create default files
        create_vibe_metadata_file(vibe)
        create_vibe_content_file(vibe)

        return {
            "success": True,
            "message": f"Vibe directory created at {vibe_dir}",
            "path": str(vibe_dir)
        }
    except Exception as e:
        logger.exception(f"Error creating vibe directory for {vibe.slug}: {str(e)}")
        return {"success": False, "message": f"Error creating vibe directory: {str(e)}"}


def delete_vibe_directory(vibe: Vibe) -> Dict[str, Any]:
    """
    Delete the directory for a vibe.

    Args:
        vibe: The Vibe object

    Returns:
        Dictionary with status and message
    """
    try:
        if not vibe.slug:
            return {"success": False, "message": "Vibe has no slug"}

        vibe_dir = get_vibe_directory(vibe.slug)

        if vibe_dir.exists():
            shutil.rmtree(vibe_dir)
            return {"success": True, "message": f"Vibe directory deleted: {vibe_dir}"}
        else:
            return {"success": True, "message": f"Vibe directory does not exist: {vibe_dir}"}
    except Exception as e:
        logger.exception(f"Error deleting vibe directory for {vibe.slug}: {str(e)}")
        return {"success": False, "message": f"Error deleting vibe directory: {str(e)}"}


def create_vibe_metadata_file(vibe: Vibe) -> Dict[str, Any]:
    """
    Create a metadata file for a vibe.

    Args:
        vibe: The Vibe object

    Returns:
        Dictionary with status and message
    """
    try:
        if not vibe.slug:
            return {"success": False, "message": "Vibe has no slug"}

        vibe_dir = ensure_vibe_directory_exists(vibe.slug)
        metadata_path = vibe_dir / "metadata.json"

        metadata = {
            "id": vibe.id,
            "title": vibe.title,
            "slug": vibe.slug,
            "description": vibe.description,
            "created_at": vibe.created_at.isoformat(),
            "updated_at": vibe.updated_at.isoformat(),
            "user_id": vibe.user.id if vibe.user else None,
            "username": vibe.user.username if vibe.user else None
        }

        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            "success": True,
            "message": f"Metadata file created at {metadata_path}",
            "path": str(metadata_path)
        }
    except Exception as e:
        logger.exception(f"Error creating metadata file for {vibe.slug}: {str(e)}")
        return {"success": False, "message": f"Error creating metadata file: {str(e)}"}


def create_vibe_content_file(vibe: Vibe) -> Dict[str, Any]:
    """
    Create a content file for a vibe, potentially using AI to generate content.

    Args:
        vibe: The Vibe object

    Returns:
        Dictionary with status and message
    """
    try:
        if not vibe.slug:
            return {"success": False, "message": "Vibe has no slug"}

        vibe_dir = ensure_vibe_directory_exists(vibe.slug)
        content_path = vibe_dir / "content.json"

        # Default content structure
        content = {
            "tagline": "",
            "elements": [],
            "color_palette": [],
            "essence": "",
            "ai_generated": False
        }

        # Try to generate content with AI if user has an API key
        if vibe.user and hasattr(vibe.user, 'profile') and vibe.user.profile.chatgpt_api_key:
            try:
                ai_result = generate_vibe_content(vibe.user, vibe.title, vibe.description)
                if ai_result.get("success", False):
                    content["ai_generated"] = True
                    content["ai_raw_content"] = ai_result.get("content", "")
                    # We'll parse the AI content in a more sophisticated way in a real implementation
            except Exception as ai_error:
                logger.error(f"Error generating AI content for {vibe.slug}: {str(ai_error)}")

        with open(content_path, 'w') as f:
            json.dump(content, f, indent=2)

        return {
            "success": True,
            "message": f"Content file created at {content_path}",
            "path": str(content_path)
        }
    except Exception as e:
        logger.exception(f"Error creating content file for {vibe.slug}: {str(e)}")
        return {"success": False, "message": f"Error creating content file: {str(e)}"}


def ensure_all_vibe_directories_exist() -> Dict[str, Any]:
    """
    Check all vibes in the database and create directories for any that don't have them.

    Returns:
        Dictionary with status and results
    """
    try:
        from .models import Vibe

        vibes = Vibe.objects.all()
        results = {
            "total": vibes.count(),
            "created": 0,
            "errors": 0,
            "error_details": []
        }

        for vibe in vibes:
            if not vibe.slug:
                results["errors"] += 1
                results["error_details"].append(f"Vibe ID {vibe.id} has no slug")
                continue

            vibe_dir = get_vibe_directory(vibe.slug)
            if not vibe_dir.exists():
                logger.info(f"Creating missing directory for vibe: {vibe.slug}")
                result = create_vibe_directory(vibe)
                if result["success"]:
                    results["created"] += 1
                else:
                    results["errors"] += 1
                    results["error_details"].append(f"Failed to create directory for {vibe.slug}: {result['message']}")

        return {
            "success": True,
            "results": results
        }
    except Exception as e:
        logger.exception(f"Error ensuring all vibe directories exist: {str(e)}")
        return {"success": False, "message": f"Error ensuring all vibe directories exist: {str(e)}"}


def get_vibe_content(vibe: Vibe) -> Dict[str, Any]:
    """
    Get the content for a vibe.

    Args:
        vibe: The Vibe object

    Returns:
        Dictionary with vibe content or error message
    """
    try:
        if not vibe.slug:
            return {"success": False, "message": "Vibe has no slug"}

        vibe_dir = get_vibe_directory(vibe.slug)

        # Check if the vibe directory exists, create it if it doesn't
        if not vibe_dir.exists():
            logger.info(f"Vibe directory doesn't exist for {vibe.slug}, creating it now")
            result = create_vibe_directory(vibe)
            if not result["success"]:
                return result

        content_path = vibe_dir / "content.json"

        if not content_path.exists():
            # Create the content file if it doesn't exist
            result = create_vibe_content_file(vibe)
            if not result["success"]:
                return result

        with open(content_path, 'r') as f:
            content = json.load(f)

        return {
            "success": True,
            "content": content
        }
    except Exception as e:
        logger.exception(f"Error getting content for {vibe.slug}: {str(e)}")
        return {"success": False, "message": f"Error getting vibe content: {str(e)}"}
