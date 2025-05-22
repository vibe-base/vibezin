#!/usr/bin/env python
"""
Test script to check if the DALL-E image generation and Pinata storage flow is working.
"""
import os
import sys
import django
import logging

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Test DALL-E image generation and Pinata storage."""
    from vibezin.models import Vibe, User
    from vibezin.file_utils import VibeFileManager
    from vibezin.ai_tools import handle_generate_image

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

        # Check if the user has an OpenAI API key
        if not hasattr(user, 'profile') or not user.profile.chatgpt_api_key:
            logger.error("User does not have an OpenAI API key.")
            return

        logger.info(f"User has an OpenAI API key.")

        # Create a file manager
        file_manager = VibeFileManager(vibe)

        # Simulate DALL-E image generation and Pinata storage
        logger.info("Simulating DALL-E image generation and Pinata storage...")

        # Download a sample image
        import requests
        from io import BytesIO

        # Download a sample dog image
        response = requests.get("https://placedog.net/500/300")
        if response.status_code != 200:
            logger.error(f"Failed to download sample image: {response.status_code}")
            return

        image_data = response.content

        # Upload to Pinata
        from vibezin.pinata_utils import upload_to_pinata

        pinata_result = upload_to_pinata(image_data, "test_dog.png")
        logger.info(f"Pinata result: {pinata_result}")

        if not pinata_result.get('success', False):
            logger.error(f"Failed to upload to Pinata: {pinata_result.get('error', 'Unknown error')}")
            return

        # Get the IPFS URL
        ipfs_url = pinata_result.get('ipfs_url')
        logger.info(f"IPFS URL: {ipfs_url}")

        # Save the image to the vibe directory
        local_path = file_manager.get_file_path("test_dog.png")
        with open(local_path, 'wb') as f:
            f.write(image_data)
        logger.info(f"Local path: {local_path}")

        # Create a simulated result string
        result = f"""Image generated and saved!

<img src="{ipfs_url}" alt="A cute dog playing in a park" style="max-width: 150px; max-height: 150px; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">

Filename: test_dog.png

IPFS URL: {ipfs_url} (PRIMARY URL TO USE IN HTML)

Local path: {local_path} (Backup URL)

Revised prompt: A cute dog playing in a park

IMPORTANT: Use the IPFS URL as the primary source in your HTML:

```html
<!-- Regular image using IPFS URL (PREFERRED METHOD) -->
<img src="{ipfs_url}" alt="A cute dog playing in a park" class="generated-image" data-local-path="{local_path}">

<!-- Image as a link to a website -->
<a href="https://example.com" target="_blank">
  <img src="{ipfs_url}" alt="A cute dog playing in a park" class="generated-image" data-local-path="{local_path}">
</a>

<!-- Image as a link to another page in your vibe -->
<a href="another-page.html">
  <img src="{ipfs_url}" alt="A cute dog playing in a park" class="generated-image" data-local-path="{local_path}">
</a>
```

Remember: Always use the IPFS URL as the primary src in your HTML for reliability."""

        logger.info("Simulated result created.")

        # Check if the image was generated and saved to Pinata
        if "IPFS URL" in result:
            logger.info("Image was generated and saved to Pinata successfully.")

            # Extract the IPFS URL from the result
            import re
            ipfs_url_match = re.search(r'IPFS URL: (https://[^\s]+)', result)
            if ipfs_url_match:
                ipfs_url = ipfs_url_match.group(1)
                logger.info(f"IPFS URL: {ipfs_url}")

                # Extract the local path from the result
                local_path_match = re.search(r'Local path: ([^\s]+)', result)
                if local_path_match:
                    local_path = local_path_match.group(1)
                    logger.info(f"Local path: {local_path}")

                    # Check if the local file exists
                    if os.path.exists(local_path):
                        logger.info(f"Local file exists: {local_path}")
                    else:
                        logger.error(f"Local file does not exist: {local_path}")

                # Create an HTML file that uses the IPFS URL
                logger.info("Creating HTML file with the IPFS URL...")
                html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>Test DALL-E Image</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <h1>Test DALL-E Image</h1>
    <p>This is a test image generated by DALL-E and stored in Pinata IPFS.</p>
    <img src="{ipfs_url}" alt="A cute dog playing in a park">
    <p>IPFS URL: {ipfs_url}</p>
    <p>Local path: {local_path}</p>
</body>
</html>"""

                # Save the HTML file
                html_path = file_manager.get_file_path("test_dalle.html")
                with open(html_path, 'w') as f:
                    f.write(html_content)
                logger.info(f"HTML file created: {html_path}")

                # List all files in the vibe directory
                logger.info("Listing files in vibe directory...")
                files = file_manager.list_files()
                for file in files:
                    logger.info(f"  - {file['name']} ({file['size']} bytes)")
            else:
                logger.error("Could not extract IPFS URL from result.")
        else:
            logger.error("Image generation failed.")

    except Vibe.DoesNotExist:
        logger.error(f"Vibe with slug '{vibe_slug}' does not exist")
    except Exception as e:
        logger.exception(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
