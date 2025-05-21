from django.core.management.base import BaseCommand
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Sets up the static directory structure for vibes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Setting up static directory structure...'))
        
        # Create the static directory if it doesn't exist
        static_dir = settings.STATICFILES_DIRS[0]
        if not os.path.exists(static_dir):
            os.makedirs(static_dir)
            self.stdout.write(self.style.SUCCESS(f'Created static directory: {static_dir}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Static directory already exists: {static_dir}'))
        
        # Create the vibes directory if it doesn't exist
        vibes_dir = settings.VIBE_CONTENT_DIR
        if not os.path.exists(vibes_dir):
            os.makedirs(vibes_dir)
            self.stdout.write(self.style.SUCCESS(f'Created vibes directory: {vibes_dir}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Vibes directory already exists: {vibes_dir}'))
        
        # Create a .gitkeep file in the vibes directory to ensure it's tracked by git
        gitkeep_path = os.path.join(vibes_dir, '.gitkeep')
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, 'w') as f:
                f.write('# This file ensures the directory is tracked by git\n')
            self.stdout.write(self.style.SUCCESS(f'Created .gitkeep file in vibes directory'))
        
        self.stdout.write(self.style.SUCCESS('Static directory structure setup complete!'))
