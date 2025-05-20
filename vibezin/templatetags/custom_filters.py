from django import template
import re

register = template.Library()

@register.filter
def extract_pinterest_handle(url):
    """Extract the handle from a Pinterest URL."""
    # Handle empty or None values
    if not url:
        return ""

    # Remove protocol and www if present
    url = url.replace('https://', '').replace('http://', '').replace('www.', '')

    # Remove pinterest.com/ prefix if present
    if 'pinterest.com/' in url:
        handle = url.split('pinterest.com/')[1]
        # Remove any trailing slashes or query parameters
        handle = handle.split('/')[0].split('?')[0]
        return handle

    # Try to match the pattern pinterest.com/username
    match = re.search(r'pinterest\.com/([^/]+)', url)
    if match:
        handle = match.group(1)
        # Remove any trailing slashes or query parameters
        handle = handle.split('/')[0].split('?')[0]
        return handle

    # If the URL doesn't contain pinterest.com, it might be just the handle
    if 'pinterest.com' not in url:
        # Remove any trailing slashes or query parameters
        handle = url.split('/')[0].split('?')[0]
        return handle

    # If all else fails, return an empty string to avoid showing the URL
    return ""

@register.filter
def split(value, delimiter):
    """Split a string by delimiter and return a list."""
    return value.split(delimiter)
