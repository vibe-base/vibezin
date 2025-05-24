from django import forms
from django.contrib.auth.models import User
from django.conf import settings
from .models import Vibe, UserProfile
from .utils import validate_image

class VibeForm(forms.ModelForm):
    class Meta:
        model = Vibe
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a title for your vibe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your vibe', 'rows': 4}),
        }

class ProfileForm(forms.ModelForm):
    # Account type fields
    account_type = forms.ChoiceField(
        choices=[('personal', 'Personal'), ('business', 'Business')],
        widget=forms.RadioSelect(attrs={'class': 'account-type-radio'}),
        initial='personal'
    )

    # Personal account fields
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your First Name'
    }))
    last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your Last Name'
    }))
    middle_initial = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'M.I.'
    }))

    # Business account fields
    business_name = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Your Business Name'
    }))

    # File upload fields
    profile_image_file = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control',
        'accept': 'image/*',
        'data-max-size': settings.MAX_PROFILE_IMAGE_SIZE
    }))
    background_image_file = forms.ImageField(required=False, widget=forms.FileInput(attrs={
        'class': 'form-control',
        'accept': 'image/*',
        'data-max-size': settings.MAX_PROFILE_IMAGE_SIZE
    }))

    # Contact information fields
    email = forms.EmailField(required=False, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'your.email@example.com'
    }))
    phone = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': '+1 (555) 123-4567'
    }))
    address = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 3,
        'placeholder': 'Your address'
    }))

    # Add social links as form fields
    x = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://x.com/yourusername'
    }))
    # Keep twitter for backward compatibility
    twitter = forms.URLField(required=False, widget=forms.HiddenInput())
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://instagram.com/yourusername'
    }))
    github = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://github.com/yourusername'
    }))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://linkedin.com/in/yourusername'
    }))
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://yourwebsite.com'
    }))
    telegram = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://t.me/yourusername'
    }))
    youtube = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://youtube.com/@yourchannel'
    }))
    twitch = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://twitch.tv/yourusername'
    }))
    kick = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://kick.com/yourusername'
    }))
    pinterest = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://pinterest.com/yourusername'
    }))
    reddit = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://reddit.com/user/yourusername'
    }))
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://facebook.com/yourusername'
    }))
    discord = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://discord.gg/yourinvite'
    }))
    tiktok = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://tiktok.com/@yourusername'
    }))
    patreon = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://patreon.com/yourusername'
    }))
    substack = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://yourusername.substack.com'
    }))
    dribbble = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://dribbble.com/yourusername'
    }))
    behance = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://behance.net/yourusername'
    }))
    medium = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://medium.com/@yourusername'
    }))
    soundcloud = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://soundcloud.com/yourusername'
    }))
    spotify = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://open.spotify.com/artist/yourid'
    }))
    stackoverflow = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://stackoverflow.com/users/yourid'
    }))
    producthunt = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://producthunt.com/@yourusername'
    }))
    notion = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://yourusername.notion.site/yourpage'
    }))
    figma = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://figma.com/@yourusername'
    }))
    devto = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://dev.to/yourusername'
    }))
    buymeacoffee = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://buymeacoffee.com/yourusername'
    }))
    bandcamp = forms.URLField(required=False, widget=forms.URLInput(attrs={
        'class': 'form-control',
        'placeholder': 'https://yourusername.bandcamp.com'
    }))

    # API Keys
    chatgpt_api_key = forms.CharField(required=False, widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'sk-xxxx... (Your OpenAI API key)',
        'autocomplete': 'new-password'
    }))

    # Add custom fields for staff users
    custom_css = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 6,
        'placeholder': '.profile-container { /* your custom styles */ }'
    }))
    custom_html = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 6,
        'placeholder': "<div class='custom-section'>Your custom HTML</div>"
    }))

    class Meta:
        model = UserProfile
        fields = ['account_type', 'first_name', 'last_name', 'middle_initial', 'business_name',
                 'email', 'phone', 'address', 'bio', 'profile_image', 'background_image', 'theme',
                 'chatgpt_api_key']
        widgets = {
            'bio': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Tell the world about yourself', 'rows': 4}),
            'profile_image': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/your-image.jpg'}),
            'background_image': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/your-background.jpg'}),
            'theme': forms.RadioSelect(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize social link fields from the instance's social_links
        if self.instance and hasattr(self.instance, 'social_links'):
            # Handle both 'twitter' and 'x' fields
            if 'twitter' in self.instance.social_links:
                self.fields['x'].initial = self.instance.social_links.get('twitter', '')
                self.fields['twitter'].initial = self.instance.social_links.get('twitter', '')
            elif 'x' in self.instance.social_links:
                self.fields['x'].initial = self.instance.social_links.get('x', '')
                self.fields['twitter'].initial = self.instance.social_links.get('x', '')

            # Initialize other social fields
            social_fields = [
                'instagram', 'github', 'linkedin', 'website', 'telegram', 'youtube', 'twitch', 'kick', 'pinterest',
                'reddit', 'facebook', 'discord', 'tiktok', 'patreon', 'substack', 'dribbble', 'behance', 'medium',
                'soundcloud', 'spotify', 'stackoverflow', 'producthunt', 'notion', 'figma', 'devto', 'buymeacoffee', 'bandcamp'
            ]
            for field in social_fields:
                self.fields[field].initial = self.instance.social_links.get(field, '')

        # Initialize custom fields for staff users
        if self.instance:
            self.fields['custom_css'].initial = self.instance.custom_css
            self.fields['custom_html'].initial = self.instance.custom_html

    def clean(self):
        cleaned_data = super().clean()
        profile_image_file = cleaned_data.get('profile_image_file')
        background_image_file = cleaned_data.get('background_image_file')

        # Validate the profile image file if one was uploaded
        if profile_image_file:
            is_valid, error_message = validate_image(profile_image_file)
            if not is_valid:
                self.add_error('profile_image_file', error_message)

        # Validate the background image file if one was uploaded
        if background_image_file:
            is_valid, error_message = validate_image(background_image_file)
            if not is_valid:
                self.add_error('background_image_file', error_message)

        return cleaned_data

    def save(self, commit=True):
        profile = super().save(commit=False)

        # Check if profile image was cleared
        old_profile_image = profile.profile_image
        new_profile_image = self.cleaned_data.get('profile_image', '')

        # Check if we have a backup URL in the form data
        backup_url = self.data.get('profile_image_backup', '')
        if backup_url and not new_profile_image:
            print(f"Form save: Using backup URL from form data: {backup_url}")
            profile.profile_image = backup_url
        # If the profile image URL was cleared intentionally, respect that
        elif old_profile_image and not new_profile_image and not self.data.get('delete_profile_image'):
            # Only clear if the delete button was clicked
            print(f"Form save: Preserving profile_image (was: {old_profile_image})")
            profile.profile_image = old_profile_image
        # If the profile image URL was cleared via delete button, clear it
        elif old_profile_image and not new_profile_image and self.data.get('delete_profile_image'):
            profile.profile_image = ''
            print(f"Form save: Clearing profile_image (was: {old_profile_image})")
            # Note: The actual deletion from IPFS will be handled in the view
        elif new_profile_image and new_profile_image != old_profile_image:
            # If a new URL was provided, make sure it's saved
            profile.profile_image = new_profile_image
            print(f"Form save: Setting profile_image to {new_profile_image}")

        # Handle background image similar to profile image
        old_background_image = profile.background_image
        new_background_image = self.cleaned_data.get('background_image', '')

        # Check if we have a backup URL in the form data for background image
        background_backup_url = self.data.get('background_image_backup', '')
        if background_backup_url and not new_background_image:
            print(f"Form save: Using background backup URL from form data: {background_backup_url}")
            profile.background_image = background_backup_url
        # If the background image URL was cleared intentionally, respect that
        elif old_background_image and not new_background_image and not self.data.get('delete_background_image'):
            # Only clear if the delete button was clicked
            print(f"Form save: Preserving background_image (was: {old_background_image})")
            profile.background_image = old_background_image
        # If the background image URL was cleared via delete button, clear it
        elif old_background_image and not new_background_image and self.data.get('delete_background_image'):
            profile.background_image = ''
            print(f"Form save: Clearing background_image (was: {old_background_image})")
            # Note: The actual deletion from IPFS will be handled in the view
        elif new_background_image and new_background_image != old_background_image:
            # If a new URL was provided, make sure it's saved
            profile.background_image = new_background_image
            print(f"Form save: Setting background_image to {new_background_image}")

        # Handle ChatGPT API key - preserve existing key if field is blank
        new_api_key = self.cleaned_data.get('chatgpt_api_key', '')
        # Get the original instance to access the current API key in the database
        original_instance = UserProfile.objects.get(pk=profile.pk) if profile.pk else None

        # Check if the delete flag is set
        delete_api_key = self.data.get('delete_api_key') == 'true'
        # Check if the preserve flag is set
        preserve_api_key = self.data.get('preserve_api_key') == 'true'

        if delete_api_key:
            # If the delete flag is set, clear the API key
            print(f"Form save: Removing ChatGPT API key")
            profile.chatgpt_api_key = ''
        elif new_api_key:
            # If a new key is provided, use it
            print(f"Form save: Setting new ChatGPT API key")
            profile.chatgpt_api_key = new_api_key
        elif preserve_api_key and original_instance and original_instance.chatgpt_api_key:
            # If the preserve flag is set and there's an existing key, preserve it
            print(f"Form save: Preserving existing ChatGPT API key")
            profile.chatgpt_api_key = original_instance.chatgpt_api_key
        elif not new_api_key and original_instance and original_instance.chatgpt_api_key:
            # If the field is blank and there's an existing key, preserve it (fallback)
            print(f"Form save: Preserving existing ChatGPT API key (fallback)")
            profile.chatgpt_api_key = original_instance.chatgpt_api_key
        # If none of the above conditions are met, the field will remain blank

        # Save social links
        social_links = {}

        # Handle X (Twitter) field - store as 'x' in the database
        if self.cleaned_data.get('x'):
            social_links['x'] = self.cleaned_data.get('x')
        elif self.cleaned_data.get('twitter'):
            # For backward compatibility
            social_links['x'] = self.cleaned_data.get('twitter')

        # Save other social links
        social_fields = [
            'instagram', 'github', 'linkedin', 'website', 'telegram', 'youtube', 'twitch', 'kick', 'pinterest',
            'reddit', 'facebook', 'discord', 'tiktok', 'patreon', 'substack', 'dribbble', 'behance', 'medium',
            'soundcloud', 'spotify', 'stackoverflow', 'producthunt', 'notion', 'figma', 'devto', 'buymeacoffee', 'bandcamp'
        ]
        for field in social_fields:
            if self.cleaned_data.get(field):
                social_links[field] = self.cleaned_data.get(field)

        profile.social_links = social_links

        # Save custom fields for staff users
        profile.custom_css = self.cleaned_data.get('custom_css', '')
        profile.custom_html = self.cleaned_data.get('custom_html', '')

        # Handle profile image upload if provided
        # Note: The actual upload to IPFS will be handled in the view
        # to avoid circular imports and to better handle request context

        if commit:
            profile.save()
        return profile

class UsernameForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choose a unique username'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_username(self):
        username = self.cleaned_data.get('username')

        # Check if username is already taken
        if User.objects.filter(username=username).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This username is already taken. Please choose another one.")

        # Check for valid characters (Django's User model already has this validation,
        # but we're adding custom error messages)
        import re
        if not re.match(r'^[\w.@+-]+$', username):
            raise forms.ValidationError("Username can only contain letters, digits, and @/./+/-/_ characters.")

        # Check minimum length
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters long.")

        # Check for reserved words or patterns you don't want as usernames
        reserved_words = ['admin', 'administrator', 'root', 'superuser', 'vibezin', 'system']
        if username.lower() in reserved_words:
            raise forms.ValidationError("This username is reserved. Please choose another one.")

        return username
