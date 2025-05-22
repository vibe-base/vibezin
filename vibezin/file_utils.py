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
        # Check if it's an image file
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        if any(filename.lower().endswith(ext) for ext in image_extensions):
            # Don't modify image filenames
            return self.vibe_dir / filename

        # Ensure the filename has a valid extension for non-image files
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

        logger.error(f"CRITICAL DEBUG: list_files called for vibe: {self.vibe.slug}")
        logger.error(f"CRITICAL DEBUG: Vibe directory: {self.vibe_dir}")
        logger.error(f"CRITICAL DEBUG: Vibe directory exists: {self.vibe_dir.exists()}")

        # Check if the directory exists
        if not self.vibe_dir.exists():
            logger.error(f"CRITICAL DEBUG: Vibe directory does not exist: {self.vibe_dir}")
            return files

        # List all files in the directory using os.listdir for debugging
        try:
            logger.error(f"CRITICAL DEBUG: Files in directory using os.listdir:")
            for filename in os.listdir(str(self.vibe_dir)):
                logger.error(f"CRITICAL DEBUG: - {filename}")
        except Exception as e:
            logger.error(f"CRITICAL DEBUG: Error listing directory with os.listdir: {str(e)}")

        # List all files in the directory using Path.iterdir()
        try:
            logger.error(f"CRITICAL DEBUG: Files in directory using Path.iterdir():")
            for file_path in self.vibe_dir.iterdir():
                logger.error(f"CRITICAL DEBUG: - {file_path.name} (is_file: {file_path.is_file()}, starts_with_dot: {file_path.name.startswith('.')})")

                if file_path.is_file() and not file_path.name.startswith('.'):
                    try:
                        file_info = {
                            'name': file_path.name,
                            'path': str(file_path),
                            'size': file_path.stat().st_size,
                            'modified': file_path.stat().st_mtime,
                            'type': file_path.suffix[1:] if file_path.suffix else 'unknown'
                        }
                        logger.error(f"CRITICAL DEBUG: Adding file to list: {file_info}")
                        files.append(file_info)
                    except Exception as e:
                        logger.error(f"CRITICAL DEBUG: Error adding file {file_path.name} to list: {str(e)}")
        except Exception as e:
            logger.error(f"CRITICAL DEBUG: Error iterating directory: {str(e)}")

        # Sort the files by name
        sorted_files = sorted(files, key=lambda x: x['name'])
        logger.error(f"CRITICAL DEBUG: Returning {len(sorted_files)} files")

        return sorted_files

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
            # Make sure the vibe directory exists
            if not self.vibe_dir.exists():
                logger.info(f"Creating vibe directory: {self.vibe_dir}")
                self.vibe_dir.mkdir(parents=True, exist_ok=True)

            file_path = self.get_file_path(filename)
            logger.info(f"Writing file: {file_path}")

            # Check if the file already exists
            file_existed = file_path.exists()
            logger.info(f"File exists: {file_existed}")

            # If the file exists, create a backup
            if file_existed:
                old_content = self.read_file(filename).get('content', '')
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                with open(backup_path, 'w') as f:
                    f.write(old_content)
                logger.info(f"Created backup: {backup_path}")

            # Write the new content
            with open(file_path, 'w') as f:
                f.write(content)
            logger.info(f"Wrote {len(content)} bytes to {file_path}")

            # Update the vibe's custom file flags
            self._update_vibe_flags(filename)

            # Verify the file was written
            if file_path.exists():
                logger.info(f"File exists after write: {file_path}")
                logger.info(f"File size: {file_path.stat().st_size} bytes")
            else:
                logger.error(f"File does not exist after write: {file_path}")
                return {
                    'success': False,
                    'error': f"File was not created: {filename}"
                }

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
            logger.info(f"Attempting to delete file: {filename}")

            # Get the file path
            file_path = self.vibe_dir / filename
            logger.info(f"File path to delete: {file_path}")

            # Check if the file exists
            if not file_path.exists():
                logger.warning(f"File does not exist: {file_path}")
                return {
                    'success': False,
                    'error': f"File {filename} does not exist"
                }

            # Delete the file
            os.remove(file_path)
            logger.info(f"File successfully deleted: {file_path}")

            # Also try to delete any backup file if it exists
            backup_path = Path(str(file_path) + ".bak")
            if backup_path.exists():
                try:
                    os.remove(backup_path)
                    logger.info(f"Backup file also deleted: {backup_path}")
                except:
                    # Ignore errors when deleting backup files
                    pass

            # Update vibe flags if necessary
            if filename.endswith('.html') or filename == 'index.html':
                # Check if there are any other HTML files
                html_files = [f for f in os.listdir(self.vibe_dir) if f.endswith('.html')]
                if not html_files:
                    logger.info(f"No more HTML files, setting has_custom_html to False for vibe: {self.vibe.slug}")
                    self.vibe.has_custom_html = False
                    self.vibe.save()

            elif filename.endswith('.css'):
                # Check if there are any other CSS files
                css_files = [f for f in os.listdir(self.vibe_dir) if f.endswith('.css')]
                if not css_files:
                    logger.info(f"No more CSS files, setting has_custom_css to False for vibe: {self.vibe.slug}")
                    self.vibe.has_custom_css = False
                    self.vibe.save()

            elif filename.endswith('.js'):
                # Check if there are any other JS files
                js_files = [f for f in os.listdir(self.vibe_dir) if f.endswith('.js')]
                if not js_files:
                    logger.info(f"No more JS files, setting has_custom_js to False for vibe: {self.vibe.slug}")
                    self.vibe.has_custom_js = False
                    self.vibe.save()

            return {
                'success': True,
                'message': f"File deleted: {filename}",
                'path': str(file_path),
                'name': filename
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
