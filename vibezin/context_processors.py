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
        has_providers = providers.exists()
        print(f"Social providers found: {has_providers}, Count: {providers.count()}")
        if has_providers:
            for provider in providers:
                print(f"Provider: {provider.name}, Provider ID: {provider.provider}")
        return {
            'socialaccount_providers': has_providers
        }
    except Exception as e:
        print(f"Error in social_providers context processor: {str(e)}")
        # If there's an error (e.g., table doesn't exist), return False
        return {
            'socialaccount_providers': False
        }
