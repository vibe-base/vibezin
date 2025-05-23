"""
Tool processing logic for AI assistants.
"""
import logging
import uuid
import os
from typing import Dict, Any, List
from django.contrib.auth.models import User

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def explain_image_workflow() -> str:
    """
    Explain the complete workflow for generating and using images in HTML.

    This function provides a detailed explanation of the chain of reasoning
    for generating images with DALL-E, saving them to IPFS, and using them in HTML.

    Returns:
        A formatted string with the explanation
    """
    return """
# Complete Image Workflow for the O1 Reasoning Engine

## Step 1: Generate an Image with DALL-E
```tool
generate_image
prompt: A beautiful sunset over the ocean
size: 1024x1024
filename: sunset.png
```

## Step 2: Get the IPFS URL from the Response
When the image is generated, it's automatically saved to IPFS and you'll receive:
- The IPFS URL (primary URL to use in HTML)
- The local path (backup URL)

## Step 3: Use the IPFS URL in Your HTML
```tool
write_file
filename: index.html
content:
<!DOCTYPE html>
<html>
<head>
    <title>Beautiful Sunset</title>
</head>
<body>
    <h1>Beautiful Sunset</h1>
    <!-- Use the IPFS URL as the primary source -->
    <img src="https://ipfs.io/ipfs/QmExample..." alt="Beautiful sunset" class="generated-image">
</body>
</html>
```

## CRITICAL REQUIREMENTS:
1. ALWAYS use the COMPLETE, ABSOLUTE Pinata IPFS URL (starting with https://)
2. NEVER use relative paths like 'image.png' or '/static/vibes/...' for DALL-E generated images
3. The IPFS URL is the ONLY reliable way to access images across different environments
4. Local paths are ONLY for fallback and should NEVER be used as the primary src

## Examples of CORRECT image references:
✅ `<img src="https://ipfs.io/ipfs/QmExample..." alt="Description">`
✅ `<img src="https://gateway.pinata.cloud/ipfs/QmExample..." alt="Description">`

## Examples of INCORRECT image references:
❌ `<img src="sunset.png" alt="Description">` (relative path)
❌ `<img src="/static/vibes/my-vibe/sunset.png" alt="Description">` (server path)
❌ `<img src="ipfs/QmExample..." alt="Description">` (missing https://)

## Important Notes:
1. Always use the IPFS URL as the primary source in your HTML
2. The IPFS URL is more reliable and persistent than the local path
3. The complete chain is: Generate → Save to IPFS → Get URL → Use in HTML
4. When listing images, use the IPFS URLs from the results in your HTML

Follow this workflow to ensure images are properly stored and displayed.
"""


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

    logger.error(f"CRITICAL DEBUG: process_tool_calls called with content length: {len(content)}")
    logger.error(f"CRITICAL DEBUG: Vibe: {vibe.id} ({vibe.slug})")
    logger.error(f"CRITICAL DEBUG: User: {user.id} ({user.username})")
    logger.error(f"CRITICAL DEBUG: Content starts with: {content[:200]}...")
    logger.error(f"CRITICAL DEBUG: Content ends with: {content[-200:] if len(content) > 200 else content}")

    # Check if there are any tool calls in the content
    if "```tool" not in content:
        logger.error("CRITICAL DEBUG: No tool calls found in content (no ```tool marker)")
        return content

    # Split the content by tool blocks
    parts = content.split("```tool")
    logger.error(f"CRITICAL DEBUG: Found {len(parts) - 1} tool call blocks in content")
    result = [parts[0]]  # Start with the content before the first tool call

    # Create a file manager for this vibe
    try:
        file_manager = VibeFileManager(vibe)
        logger.error(f"CRITICAL DEBUG: Created file manager for vibe: {vibe.slug}")
        logger.error(f"CRITICAL DEBUG: Vibe directory: {file_manager.vibe_dir}")
        logger.error(f"CRITICAL DEBUG: Vibe directory exists: {file_manager.vibe_dir.exists()}")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error creating file manager: {str(e)}")
        return f"Error creating file manager: {str(e)}\n\n{content}"

    # Process each tool call
    for i in range(1, len(parts)):
        part = parts[i]
        logger.error(f"CRITICAL DEBUG: Processing tool call block {i}, length: {len(part)}")

        # Find the end of the tool block
        tool_end = part.find("```")
        if tool_end == -1:
            # If there's no closing tag, just append the part as is
            logger.error(f"CRITICAL DEBUG: No closing ``` found for tool call block {i}")
            result.append("```tool" + part)
            continue

        # Extract the tool call
        tool_call = part[:tool_end].strip()
        logger.error(f"CRITICAL DEBUG: Extracted tool call: {tool_call}")

        # Get the content after the tool call
        after_tool = part[tool_end + 3:]
        logger.error(f"CRITICAL DEBUG: Content after tool call: {after_tool[:100]}...")

        # Parse the tool call
        lines = tool_call.split("\n")
        tool_name = lines[0].strip()
        logger.error(f"CRITICAL DEBUG: Tool name: {tool_name}")
        logger.error(f"CRITICAL DEBUG: Tool call lines: {len(lines)}")

        # Log all lines of the tool call for debugging
        for j, line in enumerate(lines):
            logger.error(f"CRITICAL DEBUG: Tool call line {j}: {line}")

        # Execute the tool call
        tool_result = "Error: Unknown tool"
        logger.error(f"CRITICAL DEBUG: Executing tool: {tool_name} with {len(lines)} lines")

        if tool_name == "list_files":
            tool_result = handle_list_files(file_manager)
        elif tool_name == "read_file":
            tool_result = handle_read_file(file_manager, lines)
        elif tool_name == "write_file":
            logger.error(f"CRITICAL DEBUG: Calling handle_write_file with {len(lines)} lines")
            try:
                tool_result = handle_write_file(file_manager, lines)
                logger.error(f"CRITICAL DEBUG: handle_write_file result: {tool_result}")
            except Exception as e:
                error_msg = f"CRITICAL ERROR in handle_write_file: {str(e)}"
                logger.error(error_msg)
                tool_result = f"Error: {error_msg}"
        elif tool_name == "delete_file":
            tool_result = handle_delete_file(file_manager, lines)
        elif tool_name == "generate_image":
            tool_result = handle_generate_image(file_manager, lines, user)
        elif tool_name == "save_image":
            tool_result = handle_save_image(file_manager, lines)
        elif tool_name == "list_images":
            tool_result = handle_list_images(user, vibe)
        elif tool_name == "explain_image_workflow":
            tool_result = explain_image_workflow()

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

    # Add enhanced debug logging
    logger.error(f"CRITICAL DEBUG: handle_write_file called with {len(lines)} lines")
    logger.error(f"CRITICAL DEBUG: Vibe slug: {file_manager.vibe.slug}")
    logger.error(f"CRITICAL DEBUG: Vibe directory: {file_manager.vibe_dir}")
    logger.error(f"CRITICAL DEBUG: Vibe directory exists: {file_manager.vibe_dir.exists()}")
    logger.error(f"CRITICAL DEBUG: Vibe directory is writable: {os.access(file_manager.vibe_dir, os.W_OK)}")
    logger.error(f"CRITICAL DEBUG: Current working directory: {os.getcwd()}")
    logger.error(f"CRITICAL DEBUG: User running process: {os.getuid()}")
    logger.error(f"CRITICAL DEBUG: File manager type: {type(file_manager)}")
    logger.error(f"CRITICAL DEBUG: Vibe object: {file_manager.vibe}")

    # Log all lines for debugging in production
    logger.error("CRITICAL DEBUG: Full tool call content:")
    for i, line in enumerate(lines):
        logger.error(f"CRITICAL DEBUG: Line {i}: {line[:100]}...")

    # Find the filename and content
    for i, line in enumerate(lines[1:]):
        if line.startswith("filename:"):
            filename = line[len("filename:"):].strip()
            logger.error(f"CRITICAL DEBUG: Found filename: {filename}")
        elif line.startswith("content:"):
            content_start = i + 1
            logger.error(f"CRITICAL DEBUG: Found content start at line {content_start + 1}")
            break

    if not filename:
        logger.error("CRITICAL DEBUG: No filename found in tool call")
        return "Error: No filename found in tool call"

    if content_start is None:
        logger.error("CRITICAL DEBUG: No content marker found in tool call")
        return "Error: No content marker found in tool call"

    # Extract the content
    try:
        file_content = "\n".join(lines[content_start + 1:])
        logger.error(f"CRITICAL DEBUG: Extracted content (first 100 chars): {file_content[:100]}...")
        logger.error(f"CRITICAL DEBUG: Content length: {len(file_content)} characters")

        # Sanitize image URLs in HTML content
        if filename.endswith('.html'):
            try:
                from .html_utils import sanitize_image_urls, extract_image_references

                # Extract image references before sanitizing
                original_images = extract_image_references(file_content)
                logger.error(f"CRITICAL DEBUG: Found {len(original_images)} image references in HTML content")
                for img in original_images:
                    logger.error(f"CRITICAL DEBUG: Image reference: src={img['src']}, is_pinata={img['is_pinata']}")

                # Sanitize image URLs
                sanitized_content = sanitize_image_urls(file_content, file_manager.vibe.slug)

                # Extract image references after sanitizing
                sanitized_images = extract_image_references(sanitized_content)
                logger.error(f"CRITICAL DEBUG: Found {len(sanitized_images)} image references after sanitizing")
                for img in sanitized_images:
                    logger.error(f"CRITICAL DEBUG: Sanitized image reference: src={img['src']}, is_pinata={img['is_pinata']}")

                # Use the sanitized content
                file_content = sanitized_content
                logger.error(f"CRITICAL DEBUG: Using sanitized content: {len(file_content)} bytes")
            except Exception as e:
                logger.error(f"CRITICAL DEBUG: Error sanitizing image URLs: {str(e)}")
                # Continue with the original content if there's an error
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error extracting content: {str(e)}")
        return f"Error: Failed to extract content: {str(e)}"

    # Get the file path
    try:
        file_path = file_manager.get_file_path(filename)
        logger.error(f"CRITICAL DEBUG: Full file path: {file_path}")
        logger.error(f"CRITICAL DEBUG: File path type: {type(file_path)}")
        logger.error(f"CRITICAL DEBUG: File path parent: {file_path.parent}")
        logger.error(f"CRITICAL DEBUG: File path parent exists: {file_path.parent.exists()}")
        logger.error(f"CRITICAL DEBUG: File path parent is writable: {os.access(file_path.parent, os.W_OK)}")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error getting file path: {str(e)}")
        return f"Error: Failed to get file path: {str(e)}"

    # Check if the file already exists
    try:
        if file_path.exists():
            logger.error(f"CRITICAL DEBUG: File already exists: {file_path}")
            logger.error(f"CRITICAL DEBUG: File size: {file_path.stat().st_size} bytes")
            logger.error(f"CRITICAL DEBUG: File is writable: {os.access(file_path, os.W_OK)}")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error checking if file exists: {str(e)}")
        # Continue anyway, as this is just a check

    # Create the directory if it doesn't exist
    try:
        if not file_path.parent.exists():
            logger.error(f"CRITICAL DEBUG: Creating directory: {file_path.parent}")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.error(f"CRITICAL DEBUG: Directory created: {file_path.parent.exists()}")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error creating directory: {str(e)}")
        return f"Error: Failed to create directory: {str(e)}"

    # Try multiple methods to write the file
    try:
        # Method 1: Write the file directly
        logger.error(f"CRITICAL DEBUG: Writing file directly (Method 1): {file_path}")
        with open(str(file_path), 'w') as f:
            f.write(file_content)
        logger.error(f"CRITICAL DEBUG: Direct file write successful (Method 1)")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error in direct file write (Method 1): {str(e)}")

        try:
            # Method 2: Try with absolute path
            abs_path = os.path.abspath(str(file_path))
            logger.error(f"CRITICAL DEBUG: Writing file with absolute path (Method 2): {abs_path}")
            with open(abs_path, 'w') as f:
                f.write(file_content)
            logger.error(f"CRITICAL DEBUG: Absolute path file write successful (Method 2)")
        except Exception as e2:
            logger.error(f"CRITICAL DEBUG: Error in absolute path file write (Method 2): {str(e2)}")

            try:
                # Method 3: Try with os.path.join
                dir_path = str(file_path.parent)
                file_name = os.path.basename(str(file_path))
                joined_path = os.path.join(dir_path, file_name)
                logger.error(f"CRITICAL DEBUG: Writing file with os.path.join (Method 3): {joined_path}")
                with open(joined_path, 'w') as f:
                    f.write(file_content)
                logger.error(f"CRITICAL DEBUG: os.path.join file write successful (Method 3)")
            except Exception as e3:
                logger.error(f"CRITICAL DEBUG: Error in os.path.join file write (Method 3): {str(e3)}")
                return f"Error: All file write methods failed. Errors: Method 1: {str(e)}, Method 2: {str(e2)}, Method 3: {str(e3)}"

    # Check if the file was actually created
    try:
        if file_path.exists():
            logger.error(f"CRITICAL DEBUG: File exists after direct write: {file_path}")
            logger.error(f"CRITICAL DEBUG: File size after direct write: {file_path.stat().st_size} bytes")

            # Read the file back to verify content
            with open(file_path, 'r') as f:
                read_content = f.read()
            logger.error(f"CRITICAL DEBUG: Read back content length: {len(read_content)} bytes")
            logger.error(f"CRITICAL DEBUG: Content matches: {read_content == file_content}")
        else:
            logger.error(f"CRITICAL DEBUG: File does not exist after direct write: {file_path}")
            # Try to diagnose the issue
            logger.error(f"CRITICAL DEBUG: Directory exists: {file_path.parent.exists()}")
            logger.error(f"CRITICAL DEBUG: Directory is writable: {os.access(file_path.parent, os.W_OK)}")
            logger.error(f"CRITICAL DEBUG: Checking for file with different methods:")

            # Try different methods to check if the file exists
            abs_path = os.path.abspath(str(file_path))
            logger.error(f"CRITICAL DEBUG: File exists (absolute path): {os.path.exists(abs_path)}")

            dir_path = str(file_path.parent)
            file_name = os.path.basename(str(file_path))
            joined_path = os.path.join(dir_path, file_name)
            logger.error(f"CRITICAL DEBUG: File exists (os.path.join): {os.path.exists(joined_path)}")

            # List all files in the directory
            logger.error(f"CRITICAL DEBUG: Files in directory {file_path.parent}:")
            try:
                for f in os.listdir(str(file_path.parent)):
                    logger.error(f"CRITICAL DEBUG: - {f}")
            except Exception as e:
                logger.error(f"CRITICAL DEBUG: Error listing directory: {str(e)}")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error checking if file was created: {str(e)}")

    # Now use the file manager to write the file (this will handle backups, etc.)
    try:
        logger.error(f"CRITICAL DEBUG: Writing file using file_manager: {filename}")
        result_dict = file_manager.write_file(filename, file_content)
        logger.error(f"CRITICAL DEBUG: Write file result: {result_dict}")
    except Exception as e:
        logger.error(f"CRITICAL DEBUG: Error using file_manager.write_file: {str(e)}")
        return f"Error: Failed to write file using file manager: {str(e)}"

    # Check the result of the file manager write
    if result_dict.get('success', False):
        # Verify the file exists after using the file manager
        try:
            if file_path.exists():
                logger.error(f"CRITICAL DEBUG: File exists after file manager write: {file_path}")
                logger.error(f"CRITICAL DEBUG: File size after file manager write: {file_path.stat().st_size} bytes")

                # Update the vibe's custom file flags manually to be sure
                try:
                    if filename.endswith('.html'):
                        logger.error(f"CRITICAL DEBUG: Setting has_custom_html to True for vibe: {file_manager.vibe.slug}")
                        file_manager.vibe.has_custom_html = True
                        file_manager.vibe.save()
                    elif filename.endswith('.css'):
                        logger.error(f"CRITICAL DEBUG: Setting has_custom_css to True for vibe: {file_manager.vibe.slug}")
                        file_manager.vibe.has_custom_css = True
                        file_manager.vibe.save()
                    elif filename.endswith('.js'):
                        logger.error(f"CRITICAL DEBUG: Setting has_custom_js to True for vibe: {file_manager.vibe.slug}")
                        file_manager.vibe.has_custom_js = True
                        file_manager.vibe.save()
                    logger.error(f"CRITICAL DEBUG: Vibe flags updated successfully")
                except Exception as e:
                    logger.error(f"CRITICAL DEBUG: Error updating vibe flags: {str(e)}")
            else:
                logger.error(f"CRITICAL DEBUG: File does not exist after file manager write: {file_path}")
                # Try different methods to check if the file exists
                abs_path = os.path.abspath(str(file_path))
                logger.error(f"CRITICAL DEBUG: File exists (absolute path): {os.path.exists(abs_path)}")

                dir_path = str(file_path.parent)
                file_name = os.path.basename(str(file_path))
                joined_path = os.path.join(dir_path, file_name)
                logger.error(f"CRITICAL DEBUG: File exists (os.path.join): {os.path.exists(joined_path)}")
        except Exception as e:
            logger.error(f"CRITICAL DEBUG: Error verifying file after file manager write: {str(e)}")

        # Return success message
        logger.error(f"CRITICAL DEBUG: Returning success message")
        return f"File {result_dict.get('action', 'written')}: {filename}\nLocation: {file_path}\nVibe slug: {file_manager.vibe.slug}"
    else:
        logger.error(f"CRITICAL DEBUG: File manager write failed: {result_dict.get('error', 'Unknown error')}")
        return f"Error: File manager write failed: {result_dict.get('error', 'Unknown error')}"


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

    # Get the IPFS URL from the save_db_result
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

    # Create a small thumbnail preview of the image for the chat
    img_preview = f"<img src=\"{ipfs_url}\" alt=\"{prompt}\" style=\"max-width: 150px; max-height: 150px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);\">"

    return f"""Image generated and saved!

{img_preview}

Filename: {filename}

IPFS URL: {ipfs_url} (PRIMARY URL TO USE IN HTML)

Local path: {local_path} (Backup URL)

Revised prompt: {revised_prompt}

IMPORTANT: Use the IPFS URL as the primary source in your HTML:

```html
<!-- Regular image using IPFS URL (PREFERRED METHOD) -->
<img src="{ipfs_url}" alt="{prompt}" class="generated-image" data-local-path="{local_path}">

<!-- Image as a link to a website -->
<a href="https://example.com" target="_blank">
  <img src="{ipfs_url}" alt="{prompt}" class="generated-image" data-local-path="{local_path}">
</a>

<!-- Image as a link to another page in your vibe -->
<a href="another-page.html">
  <img src="{ipfs_url}" alt="{prompt}" class="generated-image" data-local-path="{local_path}">
</a>
```

Remember: Always use the IPFS URL as the primary src in your HTML for reliability."""


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

        # For saved images, we don't have an IPFS URL, so we use the local path
        # But we should make this clear in the response

        # Create a small thumbnail preview
        img_preview = f"<img src=\"{image_path}\" alt=\"Saved image\" style=\"max-width: 150px; max-height: 150px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);\">"

        return f"""Image saved successfully!

{img_preview}

Image path: {image_path} (Use this as the src in your HTML)

Note: This image was saved directly to the vibe directory and is not stored in IPFS.

You can include this image in your HTML using:

```html
<!-- Regular image -->
<img src="{image_path}" alt="Image" class="saved-image">

<!-- Image as a link to a website -->
<a href="https://example.com" target="_blank">
  <img src="{image_path}" alt="Image" class="saved-image">
</a>

<!-- Image as a link to another page in your vibe -->
<a href="another-page.html">
  <img src="{image_path}" alt="Image" class="saved-image">
</a>
```

For maximum reliability, consider generating images with DALL-E instead, which automatically stores them in IPFS."""
    else:
        return f"Error: {result_dict.get('error', 'Failed to save the image.')}"


def handle_list_images(user: User, vibe) -> str:
    """
    Handle the list_images tool call.

    This tool retrieves all images associated with the user and the current vibe,
    including both images stored in Pinata (IPFS) and images in the vibe directory.

    Args:
        user: The User object
        vibe: The Vibe object

    Returns:
        A formatted string with the list of available images
    """
    try:
        # Get images from the database (IPFS/Pinata)
        from .models import GeneratedImage

        # Get all images for this user
        user_images = GeneratedImage.objects.filter(user=user).order_by('-created_at')

        # Get images specifically for this vibe
        vibe_images = GeneratedImage.objects.filter(vibe=vibe).order_by('-created_at')

        # Get images from the vibe directory
        from .file_utils import VibeFileManager
        file_manager = VibeFileManager(vibe)
        directory_files = file_manager.list_files()

        # Filter for image files only
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
        directory_images = [
            file for file in directory_files
            if any(file['name'].lower().endswith(ext) for ext in image_extensions)
        ]

        # Format the response
        response = []

        # Add vibe-specific images first
        if vibe_images.exists():
            response.append("## Images in this vibe (from IPFS/Pinata):")
            for img in vibe_images:
                # Use image_url field from the model
                img_url = img.image_url
                # Create a small thumbnail preview
                img_preview = f"<img src=\"{img_url}\" alt=\"{img.prompt[:30]}\" style=\"max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);\">"
                response.append(f"- **{img.prompt[:50]}{'...' if len(img.prompt) > 50 else ''}** {img_preview}")
                response.append(f"  - Image URL: {img_url}")
                response.append(f"  - Created: {img.created_at.strftime('%Y-%m-%d %H:%M')}")
                response.append(f"  - HTML: `<img src=\"{img_url}\" alt=\"{img.prompt}\" class=\"generated-image\">`")
                response.append(f"  - HTML with link: `<a href=\"https://example.com\" target=\"_blank\"><img src=\"{img_url}\" alt=\"{img.prompt}\" class=\"generated-image\"></a>`")
                response.append("")

        # Add images from the vibe directory
        if directory_images:
            response.append("## Images in the vibe directory:")
            for img in directory_images:
                file_path = f"/static/vibes/{vibe.slug}/{img['name']}"
                # Create a small thumbnail preview
                img_preview = f"<img src=\"{file_path}\" alt=\"{img['name']}\" style=\"max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);\">"
                response.append(f"- **{img['name']}** {img_preview}")
                response.append(f"  - Size: {img['size']} bytes")
                response.append(f"  - Path: {file_path}")
                response.append(f"  - HTML: `<img src=\"{file_path}\" alt=\"{img['name']}\" class=\"vibe-image\">`")
                response.append(f"  - HTML with link: `<a href=\"https://example.com\" target=\"_blank\"><img src=\"{file_path}\" alt=\"{img['name']}\" class=\"vibe-image\"></a>`")
                response.append("")

        # Add other user images (not specific to this vibe)
        other_user_images = user_images.exclude(vibe=vibe)
        if other_user_images.exists():
            response.append("## Other images you've created (not in this vibe):")
            for img in other_user_images[:10]:  # Limit to 10 to avoid overwhelming
                # Use image_url field from the model
                img_url = img.image_url
                # Create a small thumbnail preview
                img_preview = f"<img src=\"{img_url}\" alt=\"{img.prompt[:30]}\" style=\"max-width: 100px; max-height: 100px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);\">"
                response.append(f"- **{img.prompt[:50]}{'...' if len(img.prompt) > 50 else ''}** {img_preview}")
                response.append(f"  - Image URL: {img_url}")
                response.append(f"  - Created: {img.created_at.strftime('%Y-%m-%d %H:%M')}")
                response.append(f"  - HTML: `<img src=\"{img_url}\" alt=\"{img.prompt}\" class=\"generated-image\">`")
                response.append(f"  - HTML with link: `<a href=\"https://example.com\" target=\"_blank\"><img src=\"{img_url}\" alt=\"{img.prompt}\" class=\"generated-image\"></a>`")
                response.append("")

            if other_user_images.count() > 10:
                response.append(f"*...and {other_user_images.count() - 10} more images not shown*")

        # Add a note about how to use these images
        response.append("## How to use these images:")
        response.append("1. Copy the HTML code for the image you want to use")
        response.append("2. Paste it into your HTML file using the write_file tool")
        response.append("3. You can modify the HTML to change the size, add classes, or make the image a link")
        response.append("4. Example of making an image link to another page: `<a href=\"another-page.html\"><img src=\"IMAGE_URL\" alt=\"Description\"></a>`")

        if not response:
            return "No images found. You can create images using the generate_image tool or save existing images using the save_image tool."

        return "\n".join(response)

    except Exception as e:
        logger.exception(f"Error listing images: {str(e)}")
        return f"Error listing images: {str(e)}"
