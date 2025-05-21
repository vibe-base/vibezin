from django.core.management.base import BaseCommand
from vibezin.vibe_utils import ensure_all_vibe_directories_exist


class Command(BaseCommand):
    help = 'Ensures that all vibes have their corresponding directories in the static folder'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting to check and create vibe directories...'))
        
        result = ensure_all_vibe_directories_exist()
        
        if result['success']:
            results = result['results']
            self.stdout.write(self.style.SUCCESS(
                f"Completed! Total vibes: {results['total']}, "
                f"Directories created: {results['created']}, "
                f"Errors: {results['errors']}"
            ))
            
            if results['errors'] > 0:
                self.stdout.write(self.style.WARNING('Error details:'))
                for error in results['error_details']:
                    self.stdout.write(self.style.WARNING(f"- {error}"))
        else:
            self.stdout.write(self.style.ERROR(f"Failed: {result['message']}"))
