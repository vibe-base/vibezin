"""
Utility functions for managing files in vibe directories.
"""
import os
import json
import logging
import difflib
import requests
import shutil
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from django.conf import settings
from .models import Vibe
from .vibe_utils import ensure_vibe_directory_exists

logger = logging.getLogger(__name__)

# Define allowed file types and their extensions
ALLOWED_FILE_TYPES = {
    'html': '.html',
    'css': '.css',
    'js': '.js',
    'json': '.json',
    'md': '.md',
    'txt': '.txt',
}

class VibeFileManager:
    """Class to manage files in a vibe directory."""

    def __init__(self, vibe: Vibe):
        """
        Initialize a file manager for a vibe.

        Args:
            vibe: The Vibe object
        """
        self.vibe = vibe
        self.vibe_dir = ensure_vibe_directory_exists(vibe.slug)

    def get_file_path(self, filename: str) -> Path:
        """
        Get the path to a file in the vibe directory.

        Args:
            filename: The name of the file

        Returns:
            Path object for the file
        """
        # Ensure the filename has a valid extension
        if not any(filename.endswith(ext) for ext in ALLOWED_FILE_TYPES.values()):
            # Try to infer the extension from the filename
            file_type = filename.split('.')[-1] if '.' in filename else None
            if file_type in ALLOWED_FILE_TYPES:
                filename = f"{filename}{ALLOWED_FILE_TYPES[file_type]}"
            else:
                # Default to HTML if no extension is provided
                filename = f"{filename}.html"

        return self.vibe_dir / filename

    def list_files(self) -> List[Dict[str, Any]]:
        """
        List all files in the vibe directory.

        Returns:
            List of dictionaries with file information
        """
        files = []

        if not self.vibe_dir.exists():
            return files

        for file_path in self.vibe_dir.iterdir():
            if file_path.is_file() and not file_path.name.startswith('.'):
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size,
                    'modified': file_path.stat().st_mtime,
                    'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
                })

        return sorted(files, key=lambda x: x['name'])

    def read_file(self, filename: str) -> Dict[str, Any]:
        """
        Read a file from the vibe directory.

        Args:
            filename: The name of the file

        Returns:
            Dictionary with file content or error message
        """
        try:
            file_path = self.get_file_path(filename)

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File {filename} does not exist"
                }

            with open(file_path, 'r') as f:
                content = f.read()

            return {
                'success': True,
                'content': content,
                'path': str(file_path),
                'name': file_path.name
            }
        except Exception as e:
            logger.exception(f"Error reading file {filename}: {str(e)}")
            return {
                'success': False,
                'error': f"Error reading file: {str(e)}"
            }

    def write_file(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Write content to a file in the vibe directory.

        Args:
            filename: The name of the file
            content: The content to write

        Returns:
            Dictionary with status and message
        """
        try:
            file_path = self.get_file_path(filename)

            # Check if the file already exists
            file_existed = file_path.exists()

            # If the file exists, create a backup
            if file_existed:
                old_content = self.read_file(filename).get('content', '')
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                with open(backup_path, 'w') as f:
                    f.write(old_content)

            # Write the new content
            with open(file_path, 'w') as f:
                f.write(content)

            # Update the vibe's custom file flags
            self._update_vibe_flags(filename)

            return {
                'success': True,
                'message': f"File {'updated' if file_existed else 'created'}: {file_path.name}",
                'path': str(file_path),
                'name': file_path.name,
                'action': 'updated' if file_existed else 'created'
            }
        except Exception as e:
            logger.exception(f"Error writing file {filename}: {str(e)}")
            return {
                'success': False,
                'error': f"Error writing file: {str(e)}"
            }

    def _update_vibe_flags(self, filename: str) -> None:
        """
        Update the vibe's custom file flags based on the file extension.

        Args:
            filename: The name of the file
        """
        try:
            # Check if the file has a recognized extension
            if filename.endswith('.html'):
                logger.info(f"Setting has_custom_html to True for vibe: {self.vibe.slug}")
                self.vibe.has_custom_html = True
                self.vibe.save()
            elif filename.endswith('.css'):
                logger.info(f"Setting has_custom_css to True for vibe: {self.vibe.slug}")
                self.vibe.has_custom_css = True
                self.vibe.save()
            elif filename.endswith('.js'):
                logger.info(f"Setting has_custom_js to True for vibe: {self.vibe.slug}")
                self.vibe.has_custom_js = True
                self.vibe.save()
        except Exception as e:
            logger.exception(f"Error updating vibe flags for {filename}: {str(e)}")

    def delete_file(self, filename: str) -> Dict[str, Any]:
        """
        Delete a file from the vibe directory.

        Args:
            filename: The name of the file

        Returns:
            Dictionary with status and message
        """
        try:
            file_path = self.get_file_path(filename)

            if not file_path.exists():
                return {
                    'success': False,
                    'error': f"File {filename} does not exist"
                }

            # Create a backup before deleting
            backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())

            # Delete the file
            file_path.unlink()

            return {
                'success': True,
                'message': f"File deleted: {file_path.name}",
                'path': str(file_path),
                'name': file_path.name
            }
        except Exception as e:
            logger.exception(f"Error deleting file {filename}: {str(e)}")
            return {
                'success': False,
                'error': f"Error deleting file: {str(e)}"
            }

    def save_image(self, image_url: str, filename: str = None) -> Dict[str, Any]:
        """
        Download an image from a URL and save it to the vibe directory.

        Args:
            image_url: URL of the image to download
            filename: Optional filename to use (if not provided, will be extracted from URL)

        Returns:
            Dictionary with status and file information
        """
        try:
            # If no filename is provided, extract it from the URL
            if not filename:
                # Get the last part of the URL path
                url_path = image_url.split('?')[0]  # Remove query parameters
                url_filename = url_path.split('/')[-1]

                # If the URL doesn't have a filename with extension, generate one
                if '.' not in url_filename:
                    filename = f"image_{len(self.list_files()) + 1}.jpg"
                else:
                    filename = url_filename

            # Make sure the filename has an image extension
            if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                filename += '.jpg'

            # Create the file path
            file_path = self.vibe_dir / filename

            # Download the image
            response = requests.get(image_url, stream=True)
            if response.status_code != 200:
                return {
                    'success': False,
                    'error': f"Failed to download image: HTTP {response.status_code}"
                }

            # Save the image to the vibe directory
            with open(file_path, 'wb') as f:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, f)

            # Return success with the file information
            return {
                'success': True,
                'message': f"Image saved: {filename}",
                'path': str(file_path),
                'name': filename,
                'url': f"/static/vibes/{self.vibe.slug}/{filename}"
            }
        except Exception as e:
            logger.exception(f"Error saving image {image_url}: {str(e)}")
            return {
                'success': False,
                'error': f"Error saving image: {str(e)}"
            }

    def get_diff(self, filename: str, new_content: str) -> Dict[str, Any]:
        """
        Get the diff between the current file content and new content.

        Args:
            filename: The name of the file
            new_content: The new content to compare

        Returns:
            Dictionary with diff information
        """
        try:
            file_path = self.get_file_path(filename)

            if not file_path.exists():
                return {
                    'success': True,
                    'diff': new_content,
                    'is_new_file': True
                }

            # Read the current content
            with open(file_path, 'r') as f:
                current_content = f.read()

            # Generate the diff
            diff = difflib.unified_diff(
                current_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=f"a/{filename}",
                tofile=f"b/{filename}"
            )

            return {
                'success': True,
                'diff': ''.join(diff),
                'is_new_file': False
            }
        except Exception as e:
            logger.exception(f"Error generating diff for {filename}: {str(e)}")
            return {
                'success': False,
                'error': f"Error generating diff: {str(e)}"
            }
