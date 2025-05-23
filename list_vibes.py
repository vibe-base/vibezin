#!/usr/bin/env python
"""
Script to list all vibes in the database.
"""
import os
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

from vibezin.models import Vibe

def main():
    """List all vibes in the database."""
    print("Available vibes:")
    for vibe in Vibe.objects.all():
        print(f"- {vibe.slug} ({vibe.title})")

if __name__ == "__main__":
    main()
