#!/usr/bin/env python
"""
Script to set up the vibe directory structure and ensure all vibes have directories.
"""
import os
import django
import sys

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vibezin_project.settings')
django.setup()

def main():
    """Run the setup commands."""
    from django.core.management import call_command
    
    print("Setting up static directory structure...")
    call_command('setup_static_dirs')
    
    print("\nEnsuring all vibes have directories...")
    call_command('ensure_vibe_directories')
    
    print("\nSetup complete!")

if __name__ == '__main__':
    main()
