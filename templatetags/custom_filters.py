from django import template
import re

register = template.Library()

@register.filter
def extract_pinterest_handle(url):
    """Extract the handle from a Pinterest URL."""
    # Try to match the pattern pinterest.com/username
    match = re.search(r'pinterest\.com/([^/]+)', url)
    if match:
        return match.group(1)
    return url
