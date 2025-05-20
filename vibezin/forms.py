from django import forms
from django.contrib.auth.models import User
from .models import Vibe

class VibeForm(forms.ModelForm):
    class Meta:
        model = Vibe
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a title for your vibe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your vibe', 'rows': 4}),
        }

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
