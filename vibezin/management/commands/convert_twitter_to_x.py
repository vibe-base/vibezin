from django.core.management.base import BaseCommand
from vibezin.models import UserProfile


class Command(BaseCommand):
    help = 'Converts Twitter social links to X in all user profiles'

    def handle(self, *args, **options):
        self.stdout.write("Converting Twitter social links to X...")
        
        # Get all profiles
        profiles = UserProfile.objects.all()
        self.stdout.write(f"Found {profiles.count()} profiles")
        
        # Count of profiles updated
        updated_count = 0
        
        # Process each profile
        for profile in profiles:
            social_links = profile.social_links
            
            # Check if profile has a Twitter link
            if 'twitter' in social_links:
                # Add the same URL as an 'x' link
                social_links['x'] = social_links['twitter']
                # Remove the 'twitter' link
                del social_links['twitter']
                
                # Save the updated social_links
                profile.social_links = social_links
                profile.save()
                
                updated_count += 1
                self.stdout.write(f"Updated profile for user: {profile.user.username}")
        
        # Summary
        if updated_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Successfully converted {updated_count} Twitter links to X"))
        else:
            self.stdout.write(self.style.SUCCESS("No Twitter links found to convert"))
