#!/usr/bin/env python
"""
Script to check the current vibe and conversation in the AI builder.
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
    """Check the current vibe and conversation."""
    from vibezin.models import Vibe, VibeConversationHistory

    # Get all vibes
    vibes = Vibe.objects.all()
    logger.info(f"Found {len(vibes)} vibes:")
    for vibe in vibes:
        logger.info(f"  - ID: {vibe.id}, Slug: {vibe.slug}, Title: {vibe.title}")

    # Get all conversations
    conversations = VibeConversationHistory.objects.all().order_by('-created_at')
    logger.info(f"Found {len(conversations)} conversations:")
    for conv in conversations:
        logger.info(f"  - ID: {conv.id}, Vibe: {conv.vibe.slug if conv.vibe else 'None'}, Created: {conv.created_at}")
        logger.info(f"    - Content (first 100 chars): {conv.content[:100] if conv.content else 'No content'}...")

if __name__ == "__main__":
    main()
