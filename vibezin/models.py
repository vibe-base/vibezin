import logging
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Create your models here.
class Vibe(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vibes', null=True, blank=True)

    # New fields for AI-generated content
    has_custom_html = models.BooleanField(default=False)
    has_custom_css = models.BooleanField(default=False)
    has_custom_js = models.BooleanField(default=False)

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


class VibeConversationHistory(models.Model):
    """Model to store conversation history for a vibe."""
    vibe = models.ForeignKey(Vibe, on_delete=models.CASCADE, related_name='conversations')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vibe_conversations')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Store the conversation as JSON
    conversation = models.JSONField(default=list)

    # Track the number of messages
    message_count = models.IntegerField(default=0)

    # Track the last message timestamp
    last_message_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vibe conversation histories"
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation for {self.vibe.title} by {self.user.username}"

    def add_message(self, role: str, content: str, **kwargs) -> None:
        """
        Add a message to the conversation history.

        Args:
            role: The role of the message sender (system, user, assistant, tool)
            content: The content of the message
            **kwargs: Additional fields for the message (e.g., tool_call_id, name for tool messages)
        """
        message = {
            "role": role,
            "content": content,
            "timestamp": timezone.now().isoformat()
        }

        # Add any additional fields for special message types
        if role == "tool":
            # Tool messages require tool_call_id and name
            if "tool_call_id" not in kwargs or "name" not in kwargs:
                logger.warning("Attempted to add a tool message without required fields (tool_call_id, name)")
                return

            # Validate that there's a preceding assistant message with tool_calls
            # This is required by the OpenAI API
            tool_call_id = kwargs["tool_call_id"]
            found_matching_tool_call = False

            # Check the conversation for a matching tool call
            for prev_msg in reversed(self.conversation):
                if prev_msg.get("role") == "assistant" and "tool_calls" in prev_msg:
                    # Look for a matching tool_call_id
                    for tool_call in prev_msg["tool_calls"]:
                        if tool_call.get("id") == tool_call_id:
                            found_matching_tool_call = True
                            break
                    if found_matching_tool_call:
                        break

            if not found_matching_tool_call:
                logger.warning(f"Attempted to add a tool message with tool_call_id {tool_call_id} but no matching tool call was found in the conversation history")
                # We'll still add the message, but log the warning

            message["tool_call_id"] = tool_call_id
            message["name"] = kwargs["name"]

        # Add any other additional fields
        for key, value in kwargs.items():
            if key not in message:
                message[key] = value

        # Add the message to the conversation
        conversation = self.conversation
        conversation.append(message)
        self.conversation = conversation

        # Update the message count
        self.message_count = len(conversation)

        # Save the changes
        self.save()

    def clean_conversation_history(self):
        """
        Clean up the conversation history to ensure it's valid for the OpenAI API.

        This method:
        1. Ensures tool messages have corresponding tool calls
        2. Removes any invalid tool messages
        3. Preserves the conversation flow

        Returns:
            bool: True if changes were made, False otherwise
        """
        if not self.conversation:
            return False

        cleaned_conversation = []
        changes_made = False
        tool_call_ids = set()

        # First pass: collect all tool_call_ids from assistant messages
        for msg in self.conversation:
            if msg.get("role") == "assistant" and "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    if "id" in tool_call:
                        tool_call_ids.add(tool_call["id"])

        # Second pass: build a clean conversation history
        for msg in self.conversation:
            # Skip tool messages without a matching tool_call_id
            if msg.get("role") == "tool":
                tool_call_id = msg.get("tool_call_id")
                if not tool_call_id or tool_call_id not in tool_call_ids:
                    logger.warning(f"Removing invalid tool message with tool_call_id: {tool_call_id}")
                    changes_made = True
                    continue

            # Keep all other messages
            cleaned_conversation.append(msg)

        # Update the conversation if changes were made
        if changes_made:
            self.conversation = cleaned_conversation
            self.message_count = len(cleaned_conversation)
            self.save()
            logger.info(f"Cleaned conversation history, removed {len(self.conversation) - len(cleaned_conversation)} invalid messages")

        return changes_made

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


class GeneratedImage(models.Model):
    """Model to store AI-generated images."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_images')
    vibe = models.ForeignKey(Vibe, on_delete=models.CASCADE, related_name='images', null=True, blank=True)
    prompt = models.TextField(help_text="The original prompt used to generate the image")
    revised_prompt = models.TextField(blank=True, help_text="The revised prompt used by DALL-E")
    image_url = models.URLField(help_text="URL to the generated image")
    model = models.CharField(max_length=50, default="dall-e-3", help_text="The AI model used to generate the image")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Generated Image"
        verbose_name_plural = "Generated Images"

    def __str__(self):
        return f"Image by {self.user.username} - {self.prompt[:30]}..."
