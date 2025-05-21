import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Sets up social authentication providers'

    def handle(self, *args, **options):
        # Get or create the default site
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'vibezin.com',
                'name': 'Vibezin'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created site: {site.domain}'))
        else:
            # Update the site domain if it exists
            site.domain = 'vibezin.com'
            site.name = 'Vibezin'
            site.save()
            self.stdout.write(self.style.SUCCESS(f'Updated site: {site.domain}'))

        # Set up Google provider
        google_client_id = os.environ.get('GOOGLE_CLIENT_ID', '')
        google_secret = os.environ.get('GOOGLE_CLIENT_SECRET', '')

        if not google_client_id or not google_secret:
            self.stdout.write(self.style.WARNING(
                'Google OAuth credentials not found in environment variables. '
                'Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.'
            ))
            # Create placeholder values for development
            google_client_id = 'your-google-client-id'
            google_secret = 'your-google-secret-key'

        # Create or update Google provider
        google_app, created = SocialApp.objects.update_or_create(
            provider='google',
            defaults={
                'name': 'Google',
                'client_id': google_client_id,
                'secret': google_secret,
                'key': ''
            }
        )

        # Add the site to the provider
        google_app.sites.add(site)

        if created:
            self.stdout.write(self.style.SUCCESS('Created Google social application'))
        else:
            self.stdout.write(self.style.SUCCESS('Updated Google social application'))

        self.stdout.write(self.style.SUCCESS(
            'Social authentication setup complete. '
            'Make sure to set the correct OAuth credentials in the Django admin.'
        ))
