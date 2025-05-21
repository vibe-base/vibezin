from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
class Vibe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vibes', null=True, blank=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Generate a slug from the title if one doesn't exist
        if not self.slug:
            # Create a base slug from the title
            base_slug = slugify(self.title)

            # Check if the slug already exists
            slug = base_slug
            counter = 1
            while Vibe.objects.filter(slug=slug).exists():
                # If the slug exists, append a number to make it unique
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

class UserProfile(models.Model):
    ACCOUNT_TYPES = (
        ('personal', 'Personal'),
        ('business', 'Business'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    profile_image = models.URLField(blank=True)
    background_image = models.URLField(blank=True)
    custom_css = models.TextField(blank=True, help_text="Custom CSS for your profile page")
    custom_html = models.TextField(blank=True, help_text="Custom HTML for your profile page")
    theme = models.CharField(max_length=50, default="default")
    social_links = models.JSONField(default=dict, blank=True)

    # New fields
    account_type = models.CharField(max_length=10, choices=ACCOUNT_TYPES, default='personal')
    # Personal account fields
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    middle_initial = models.CharField(max_length=5, blank=True)
    # Business account fields
    business_name = models.CharField(max_length=100, blank=True)
    # Common fields
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(max_length=200, blank=True)

    # API Keys
    chatgpt_api_key = models.CharField(max_length=255, blank=True, help_text="Your ChatGPT API key for AI features")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    # Skip this on user creation as the profile is created and saved by create_user_profile
    if not created:
        # Check if profile exists before trying to save it
        try:
            if hasattr(instance, 'profile'):
                instance.profile.save()
        except UserProfile.DoesNotExist:
            # Create profile if it doesn't exist
            UserProfile.objects.create(user=instance)
