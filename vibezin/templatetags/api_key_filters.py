from django import template

register = template.Library()

@register.filter
def mask_api_key(api_key):
    """
    Masks an API key, showing only the first 3 and last 4 characters.
    Example: sk-abcdefghijklmnop -> sk-abc...mnop
    
    If the API key is less than 10 characters, returns a generic placeholder.
    """
    if not api_key:
        return ""
    
    if len(api_key) < 10:
        return "sk-xxx...xxx"
    
    # Show first 3 and last 4 characters
    prefix = api_key[:3]
    suffix = api_key[-4:]
    return f"{prefix}...{suffix}"
