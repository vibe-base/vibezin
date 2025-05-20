from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from vibezin.models import UserProfile


class Command(BaseCommand):
    help = 'Verifies that all users have profiles with the correct fields'

    def handle(self, *args, **options):
        self.stdout.write("Verifying user profiles...")
        
        # Get all users
        users = User.objects.all()
        self.stdout.write(f"Found {users.count()} users")
        
        # Check each user for a profile
        users_without_profile = []
        profiles_with_issues = []
        
        for user in users:
            try:
                # Try to access the profile
                profile = user.profile
                
                # Check if profile has all required fields
                issues = []
                
                # Check if social_links is a dictionary
                if not isinstance(profile.social_links, dict):
                    issues.append(f"social_links is not a dictionary: {type(profile.social_links)}")
                
                # Check if theme is valid
                valid_themes = ['default', 'dark', 'neon', 'retro', 'minimal']
                if profile.theme not in valid_themes:
                    issues.append(f"theme '{profile.theme}' is not valid")
                
                if issues:
                    profiles_with_issues.append((user, issues))
                    
            except UserProfile.DoesNotExist:
                users_without_profile.append(user)
        
        # Report results
        if users_without_profile:
            self.stdout.write(self.style.WARNING(f"Found {len(users_without_profile)} users without profiles:"))
            for user in users_without_profile:
                self.stdout.write(f"  - {user.username} (ID: {user.id})")
            
            # Create profiles for users that don't have one
            for user in users_without_profile:
                UserProfile.objects.create(user=user)
                self.stdout.write(self.style.SUCCESS(f"Created profile for user: {user.username}"))
        else:
            self.stdout.write(self.style.SUCCESS("All users have profiles"))
        
        if profiles_with_issues:
            self.stdout.write(self.style.WARNING(f"Found {len(profiles_with_issues)} profiles with issues:"))
            for user, issues in profiles_with_issues:
                self.stdout.write(f"  - {user.username} (ID: {user.id}):")
                for issue in issues:
                    self.stdout.write(f"    - {issue}")
                
                # Fix issues
                profile = user.profile
                if not isinstance(profile.social_links, dict):
                    profile.social_links = {}
                    self.stdout.write(self.style.SUCCESS(f"    Fixed social_links for {user.username}"))
                
                if profile.theme not in ['default', 'dark', 'neon', 'retro', 'minimal']:
                    profile.theme = 'default'
                    self.stdout.write(self.style.SUCCESS(f"    Fixed theme for {user.username}"))
                
                profile.save()
        else:
            self.stdout.write(self.style.SUCCESS("All profiles have valid fields"))
        
        # Show a summary of profiles
        self.stdout.write("\nProfile Summary:")
        profiles = UserProfile.objects.all()
        
        # Count themes
        theme_counts = {}
        for profile in profiles:
            theme = profile.theme
            theme_counts[theme] = theme_counts.get(theme, 0) + 1
        
        self.stdout.write("Theme usage:")
        for theme, count in theme_counts.items():
            self.stdout.write(f"  - {theme}: {count}")
        
        # Count social links
        social_counts = {}
        for profile in profiles:
            for platform in profile.social_links.keys():
                social_counts[platform] = social_counts.get(platform, 0) + 1
        
        if social_counts:
            self.stdout.write("Social links usage:")
            for platform, count in social_counts.items():
                self.stdout.write(f"  - {platform}: {count}")
        else:
            self.stdout.write("No social links found in any profiles")
