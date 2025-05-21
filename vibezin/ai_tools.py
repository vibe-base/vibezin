"""
Tool processing logic for AI assistants.
"""
import logging
import uuid
from typing import Dict, Any, List
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

def process_tool_calls(content: str, vibe, user: User) -> str:
    """
    Process tool calls in the AI response.

    Args:
        content: The content from the AI response
        vibe: The Vibe object
        user: The User object

    Returns:
        Processed content with tool call results
    """
    from .file_utils import VibeFileManager

    # Check if there are any tool calls in the content
    if "```tool" not in content:
        return content

    # Split the content by tool blocks
    parts = content.split("```tool")
    result = [parts[0]]  # Start with the content before the first tool call

    # Create a file manager for this vibe
    file_manager = VibeFileManager(vibe)

    # Process each tool call
    for i in range(1, len(parts)):
        part = parts[i]
        # Find the end of the tool block
        tool_end = part.find("```")
        if tool_end == -1:
            # If there's no closing tag, just append the part as is
            result.append("```tool" + part)
            continue

        # Extract the tool call
        tool_call = part[:tool_end].strip()
        # Get the content after the tool call
        after_tool = part[tool_end + 3:]

        # Parse the tool call
        lines = tool_call.split("\n")
        tool_name = lines[0].strip()

        # Execute the tool call
        tool_result = "Error: Unknown tool"

        if tool_name == "list_files":
            tool_result = handle_list_files(file_manager)
        elif tool_name == "read_file":
            tool_result = handle_read_file(file_manager, lines)
        elif tool_name == "write_file":
            tool_result = handle_write_file(file_manager, lines)
        elif tool_name == "delete_file":
            tool_result = handle_delete_file(file_manager, lines)
        elif tool_name == "generate_image":
            tool_result = handle_generate_image(file_manager, lines, user)
        elif tool_name == "save_image":
            tool_result = handle_save_image(file_manager, lines)

        # Append the tool result and the content after the tool call
        result.append(f"Tool result:\n{tool_result}\n\n{after_tool}")

    return "".join(result)


def handle_list_files(file_manager) -> str:
    """Handle the list_files tool call."""
    files = file_manager.list_files()
    if files:
        tool_result = "Files in the vibe directory:\n"
        for file in files:
            tool_result += f"- {file['name']} ({file['size']} bytes)\n"
    else:
        tool_result = "No files found in the vibe directory."
    return tool_result


def handle_read_file(file_manager, lines: List[str]) -> str:
    """Handle the read_file tool call."""
    filename = None
    for line in lines[1:]:
        if line.startswith("filename:"):
            filename = line[len("filename:"):].strip()
            break

    if filename:
        result_dict = file_manager.read_file(filename)
        if result_dict.get('success', False):
            return f"Content of {filename}:\n\n```\n{result_dict['content']}\n```"
        else:
            return f"Error: {result_dict.get('error', 'Unknown error')}"
    else:
        return "Error: No filename provided for read_file"


def handle_write_file(file_manager, lines: List[str]) -> str:
    """Handle the write_file tool call."""
    filename = None
    content_start = None

    # Find the filename and content
    for i, line in enumerate(lines[1:]):
        if line.startswith("filename:"):
            filename = line[len("filename:"):].strip()
        elif line.startswith("content:"):
            content_start = i + 1
            break

    if filename and content_start is not None:
        # Extract the content
        file_content = "\n".join(lines[content_start + 1:])

        # Write the file
        result_dict = file_manager.write_file(filename, file_content)
        if result_dict.get('success', False):
            return f"File {result_dict.get('action', 'written')}: {filename}"
        else:
            return f"Error: {result_dict.get('error', 'Unknown error')}"
    else:
        return "Error: Missing filename or content for write_file"


def handle_delete_file(file_manager, lines: List[str]) -> str:
    """Handle the delete_file tool call."""
    filename = None
    for line in lines[1:]:
        if line.startswith("filename:"):
            filename = line[len("filename:"):].strip()
            break

    if filename:
        result_dict = file_manager.delete_file(filename)
        if result_dict.get('success', False):
            return f"File deleted: {filename}"
        else:
            return f"Error: {result_dict.get('error', 'Unknown error')}"
    else:
        return "Error: No filename provided for delete_file"


def handle_generate_image(file_manager, lines: List[str], user: User) -> str:
    """Handle the generate_image tool call."""
    from .image_utils import generate_image, save_generated_image
    
    prompt = None
    size = "1024x1024"
    quality = "standard"
    filename = None

    for line in lines[1:]:
        if line.startswith("prompt:"):
            prompt = line[len("prompt:"):].strip()
        elif line.startswith("size:"):
            size = line[len("size:"):].strip()
        elif line.startswith("quality:"):
            quality = line[len("quality:"):].strip()
        elif line.startswith("filename:"):
            filename = line[len("filename:"):].strip()

    if not prompt:
        return "Error: No prompt provided for generate_image"
    
    # Check if the user has an OpenAI API key
    if not user.profile.chatgpt_api_key:
        return "Error: You need to add an OpenAI API key to your profile to generate images."
    
    # Generate the image
    api_key = user.profile.chatgpt_api_key
    image_result = generate_image(api_key, prompt, size, quality)

    if not image_result.get('success', False):
        return f"Error: {image_result.get('error', 'Failed to generate image.')}"
    
    # Get the image URL from DALL-E
    image_url = image_result.get('image_url')
    revised_prompt = image_result.get('revised_prompt', prompt)

    # Generate a filename if not provided
    if not filename:
        filename = f"dalle_{uuid.uuid4()}.png"
    
    # Make sure the filename has an image extension
    if not any(filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        filename += '.png'

    # First save to IPFS and database for tracking
    save_db_result = save_generated_image(
        user=user,
        prompt=prompt,
        image_url=image_url,
        revised_prompt=revised_prompt
    )

    if not save_db_result.get('success', False):
        return f"Error: {save_db_result.get('error', 'Failed to save the generated image to IPFS.')}"
    
    # Get the IPFS URL
    ipfs_url = save_db_result.get('image_url')
    
    # Associate the image with the vibe
    from .models import GeneratedImage
    image = GeneratedImage.objects.get(id=save_db_result.get('image_id'))
    image.vibe = file_manager.vibe
    image.save()

    # Also save to the vibe directory for local access
    save_result = file_manager.save_image(image_url, filename)

    if not save_result.get('success', False):
        return f"Image saved to IPFS but failed to save to vibe folder: {save_result.get('error', 'Unknown error')}\n\nIPFS URL: {ipfs_url}"
    
    # Return both the local path and IPFS URL
    local_path = save_result.get('url')

    # Create a small preview of the image for the chat
    img_preview = f"<img src=\"{ipfs_url}\" alt=\"{prompt}\" style=\"max-width: 300px; max-height: 300px;\">"

    return f"Image generated and saved!\n\n{img_preview}\n\nFilename: {filename}\n\nLocal path: {local_path}\n\nIPFS URL: {ipfs_url}\n\nRevised prompt: {revised_prompt}\n\nYou can include this image in your HTML using:\n\n```html\n<img src=\"{local_path}\" alt=\"{prompt}\" class=\"generated-image\" data-ipfs-url=\"{ipfs_url}\">\n```"


def handle_save_image(file_manager, lines: List[str]) -> str:
    """Handle the save_image tool call."""
    url = None
    filename = None

    for line in lines[1:]:
        if line.startswith("url:"):
            url = line[len("url:"):].strip()
        elif line.startswith("filename:"):
            filename = line[len("filename:"):].strip()

    if not url:
        return "Error: No URL provided for save_image"
    
    # Save the image
    result_dict = file_manager.save_image(url, filename)

    if result_dict.get('success', False):
        image_path = result_dict.get('url')
        return f"Image saved successfully!\n\nImage path: {image_path}\n\nYou can include this image in your HTML using:\n\n```html\n<img src=\"{image_path}\" alt=\"Image\" class=\"saved-image\">\n```"
    else:
        return f"Error: {result_dict.get('error', 'Failed to save the image.')}"
