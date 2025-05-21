#!/usr/bin/env python
"""
Test script to check if the AI can write files to the vibe directory.
"""
import os
import django
import logging

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def main():
    """Test writing a file to a vibe directory."""
    from vibezin.models import Vibe
    from vibezin.file_utils import VibeFileManager
    from vibezin.ai_tools import handle_write_file

    # Get the first vibe
    vibe = Vibe.objects.first()
    if not vibe:
        logger.error("No vibes found in the database.")
        return

    logger.info(f"Using vibe: {vibe.title} (slug: {vibe.slug})")

    # Create a file manager
    file_manager = VibeFileManager(vibe)

    # Create a test file
    test_content = """<!DOCTYPE html>
<html>
<head>
    <title>Test File</title>
</head>
<body>
    <h1>Test File</h1>
    <p>This is a test file created by the test script.</p>
    <img src="https://example.com/image.jpg" alt="Test Image">
</body>
</html>"""

    # Write the file using the handle_write_file function
    lines = [
        "write_file",
        "filename: test_script.html",
        "content:",
        test_content
    ]

    logger.info("Calling handle_write_file...")
    result = handle_write_file(file_manager, lines)
    logger.info(f"Result: {result}")

    # Check if the file was created
    file_path = os.path.join("static", "vibes", vibe.slug, "test_script.html")
    if os.path.exists(file_path):
        logger.info(f"File created successfully at: {file_path}")
        with open(file_path, "r") as f:
            content = f.read()
        logger.info(f"File content (first 100 chars): {content[:100]}...")
    else:
        logger.error(f"File not created at: {file_path}")

if __name__ == "__main__":
    main()
