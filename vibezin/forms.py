from django import forms
from .models import Vibe

class VibeForm(forms.ModelForm):
    class Meta:
        model = Vibe
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter a title for your vibe'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Describe your vibe', 'rows': 4}),
        }
