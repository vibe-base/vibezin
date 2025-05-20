from django import template
import re

register = template.Library()

@register.filter
def extract_pinterest_handle(url):
    """Extract the handle from a Pinterest URL."""
    # Remove protocol and www if present
    url = url.replace('https://', '').replace('http://', '').replace('www.', '')

    # Try to match the pattern pinterest.com/username
    match = re.search(r'pinterest\.com/([^/]+)', url)
    if match:
        handle = match.group(1)
        # Remove any trailing slashes or query parameters
        handle = handle.split('/')[0].split('?')[0]
        return handle

    # If no match found, try to extract from the URL directly
    if 'pinterest.com' in url:
        parts = url.split('pinterest.com/')
        if len(parts) > 1:
            handle = parts[1].split('/')[0].split('?')[0]
            return handle

    # If all else fails, return the original URL
    return url

@register.filter
def split(value, delimiter):
    """Split a string by delimiter and return a list."""
    return value.split(delimiter)
