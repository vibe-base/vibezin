"""
Tool processing logic for AI assistants.
"""
import logging
import uuid
from typing import Dict, Any, List
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

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

    # Create a small preview of the image for the chat
    img_preview = f"<img src=\"{ipfs_url}\" alt=\"{prompt}\" style=\"max-width: 300px; max-height: 300px;\">"

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
        return f"""Image saved successfully!

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
                response.append(f"- **{img.prompt[:50]}{'...' if len(img.prompt) > 50 else ''}**")
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
                response.append(f"- **{img['name']}**")
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
                response.append(f"- **{img.prompt[:50]}{'...' if len(img.prompt) > 50 else ''}**")
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
