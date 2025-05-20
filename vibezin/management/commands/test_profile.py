from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from vibezin.models import UserProfile
import json


class Command(BaseCommand):
    help = 'Tests the UserProfile model by creating and updating a profile'

    def handle(self, *args, **options):
        self.stdout.write("Testing UserProfile model...")
        
        # Get the first user
        try:
            user = User.objects.first()
            if not user:
                self.stdout.write(self.style.ERROR("No users found in the database"))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting user: {e}"))
            return
        
        self.stdout.write(f"Using user: {user.username} (ID: {user.id})")
        
        # Get or create the user's profile
        try:
            profile, created = UserProfile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f"Created new profile for {user.username}")
            else:
                self.stdout.write(f"Found existing profile for {user.username}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error getting/creating profile: {e}"))
            return
        
        # Display current profile data
        self.stdout.write("\nCurrent profile data:")
        self.stdout.write(f"Bio: {profile.bio}")
        self.stdout.write(f"Profile Image: {profile.profile_image}")
        self.stdout.write(f"Background Image: {profile.background_image}")
        self.stdout.write(f"Theme: {profile.theme}")
        self.stdout.write(f"Social Links: {json.dumps(profile.social_links, indent=2)}")
        self.stdout.write(f"Custom CSS: {len(profile.custom_css)} characters")
        self.stdout.write(f"Custom HTML: {len(profile.custom_html)} characters")
        
        # Update the profile with test data
        self.stdout.write("\nUpdating profile with test data...")
        try:
            profile.bio = "This is a test bio for profile testing"
            profile.profile_image = "https://example.com/test-profile-image.jpg"
            profile.background_image = "https://example.com/test-background-image.jpg"
            profile.theme = "neon"
            profile.social_links = {
                "twitter": "https://twitter.com/testuser",
                "github": "https://github.com/testuser",
                "website": "https://example.com"
            }
            profile.custom_css = ".test { color: red; }"
            profile.custom_html = "<div class='test'>Test HTML</div>"
            profile.save()
            self.stdout.write(self.style.SUCCESS("Profile updated successfully"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error updating profile: {e}"))
            return
        
        # Verify the update by fetching the profile again
        self.stdout.write("\nVerifying update by fetching profile from database...")
        try:
            fresh_profile = UserProfile.objects.get(pk=profile.pk)
            self.stdout.write(f"Bio: {fresh_profile.bio}")
            self.stdout.write(f"Profile Image: {fresh_profile.profile_image}")
            self.stdout.write(f"Background Image: {fresh_profile.background_image}")
            self.stdout.write(f"Theme: {fresh_profile.theme}")
            self.stdout.write(f"Social Links: {json.dumps(fresh_profile.social_links, indent=2)}")
            self.stdout.write(f"Custom CSS: {fresh_profile.custom_css}")
            self.stdout.write(f"Custom HTML: {fresh_profile.custom_html}")
            
            # Check if all fields were saved correctly
            all_correct = (
                fresh_profile.bio == "This is a test bio for profile testing" and
                fresh_profile.profile_image == "https://example.com/test-profile-image.jpg" and
                fresh_profile.background_image == "https://example.com/test-background-image.jpg" and
                fresh_profile.theme == "neon" and
                fresh_profile.social_links.get("twitter") == "https://twitter.com/testuser" and
                fresh_profile.social_links.get("github") == "https://github.com/testuser" and
                fresh_profile.social_links.get("website") == "https://example.com" and
                fresh_profile.custom_css == ".test { color: red; }" and
                fresh_profile.custom_html == "<div class='test'>Test HTML</div>"
            )
            
            if all_correct:
                self.stdout.write(self.style.SUCCESS("\nAll fields were saved correctly!"))
            else:
                self.stdout.write(self.style.ERROR("\nSome fields were not saved correctly!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error verifying profile update: {e}"))
            return
