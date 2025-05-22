#!/usr/bin/env python
"""
Debug script to test the AI file saving functionality.
"""
import os
import sys
import django
import logging
import json
from pathlib import Path

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Debug the AI file saving functionality."""
    from vibezin.models import Vibe, User, VibeConversationHistory
    from vibezin.file_utils import VibeFileManager
    from vibezin.ai_tools import process_tool_calls
    
    # Get the vibe slug from command line arguments
    if len(sys.argv) > 1:
        vibe_slug = sys.argv[1]
    else:
        # Get the first vibe
        vibe = Vibe.objects.first()
        if vibe:
            vibe_slug = vibe.slug
        else:
            logger.error("No vibes found in the database.")
            return
    
    try:
        # Get the vibe
        vibe = Vibe.objects.get(slug=vibe_slug)
        logger.info(f"Using vibe: {vibe.title} (slug: {vibe.slug})")
        
        # Get the user
        user = vibe.user
        if not user:
            logger.error("Vibe has no user.")
            return
        
        logger.info(f"Using user: {user.username}")
        
        # Create a file manager
        file_manager = VibeFileManager(vibe)
        
        # Get the vibe directory
        vibe_dir = file_manager.vibe_dir
        logger.info(f"Vibe directory: {vibe_dir}")
        
        # Check if the directory exists
        if not vibe_dir.exists():
            logger.info(f"Creating vibe directory: {vibe_dir}")
            vibe_dir.mkdir(parents=True, exist_ok=True)
        
        # List files before
        logger.info("Listing files before...")
        files_before = file_manager.list_files()
        for file in files_before:
            logger.info(f"  - {file['name']} ({file['size']} bytes)")
        
        # Get the most recent conversation history
        conversation_history = VibeConversationHistory.objects.filter(vibe=vibe).order_by('-updated_at').first()
        if not conversation_history:
            logger.error("No conversation history found.")
            return
        
        logger.info(f"Using conversation history: {conversation_history.id}")
        
        # Get the last message from the AI
        if not conversation_history.conversation:
            logger.error("Conversation history is empty.")
            return
        
        # Find the last assistant message
        assistant_messages = [msg for msg in conversation_history.conversation if msg['role'] == 'assistant']
        if not assistant_messages:
            logger.error("No assistant messages found in conversation history.")
            return
        
        last_assistant_message = assistant_messages[-1]['content']
        logger.info(f"Last assistant message (first 100 chars): {last_assistant_message[:100]}...")
        
        # Check if the message contains a write_file tool call
        if "```tool" not in last_assistant_message or "write_file" not in last_assistant_message:
            logger.error("Last assistant message does not contain a write_file tool call.")
            return
        
        # Process the tool calls in the message
        logger.info("Processing tool calls in the last assistant message...")
        processed_content = process_tool_calls(last_assistant_message, vibe, user)
        logger.info(f"Processed content (first 100 chars): {processed_content[:100]}...")
        
        # List files after
        logger.info("Listing files after...")
        files_after = file_manager.list_files()
        for file in files_after:
            logger.info(f"  - {file['name']} ({file['size']} bytes)")
        
        # Check if any new files were created
        new_files = [file for file in files_after if file['name'] not in [f['name'] for f in files_before]]
        if new_files:
            logger.info("New files created:")
            for file in new_files:
                logger.info(f"  - {file['name']} ({file['size']} bytes)")
                
                # Read the content of the new file
                file_path = file_manager.get_file_path(file['name'])
                with open(file_path, 'r') as f:
                    file_content = f.read()
                logger.info(f"  - Content (first 100 chars): {file_content[:100]}...")
        else:
            logger.warning("No new files were created.")
            
            # Extract the write_file tool call from the message
            parts = last_assistant_message.split("```tool")
            for part in parts[1:]:
                tool_end = part.find("```")
                if tool_end == -1:
                    continue
                
                tool_call = part[:tool_end].strip()
                lines = tool_call.split("\n")
                tool_name = lines[0].strip()
                
                if tool_name == "write_file":
                    logger.info(f"Found write_file tool call: {tool_call[:100]}...")
                    
                    # Extract the filename
                    filename = None
                    for line in lines[1:]:
                        if line.startswith("filename:"):
                            filename = line[len("filename:"):].strip()
                            break
                    
                    if filename:
                        logger.info(f"Filename: {filename}")
                        
                        # Check if the file exists
                        file_path = file_manager.get_file_path(filename)
                        if file_path.exists():
                            logger.info(f"File exists: {file_path}")
                            with open(file_path, 'r') as f:
                                file_content = f.read()
                            logger.info(f"Content (first 100 chars): {file_content[:100]}...")
                        else:
                            logger.error(f"File does not exist: {file_path}")
                    else:
                        logger.error("No filename found in write_file tool call.")
        
    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
