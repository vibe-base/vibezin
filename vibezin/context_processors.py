"""
Context processors for the Vibezin app.
"""
from allauth.socialaccount.models import SocialApp

def social_providers(request):
    """
    Add social account providers to the template context.
    
    This allows templates to check if social login is available.
    """
    try:
        # Check if any social apps are configured
        providers = SocialApp.objects.all()
        return {
            'socialaccount_providers': providers.exists()
        }
    except Exception:
        # If there's an error (e.g., table doesn't exist), return False
        return {
            'socialaccount_providers': False
        }
