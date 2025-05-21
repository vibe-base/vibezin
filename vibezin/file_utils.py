"""
Utility functions for managing files in vibe directories.
"""
import os
import json
import logging
import difflib
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
