from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from django.views.decorators.http import require_POST
import json
from .models import Vibe, UserProfile
from .forms import VibeForm, UsernameForm, ProfileForm
from .utils import validate_image, optimize_image, upload_to_ipfs, delete_from_ipfs
from .vibe_utils import get_vibe_content, ensure_vibe_directory_exists

@login_required
@require_POST
def upload_profile_image(request):
    """AJAX endpoint for uploading profile images to IPFS via Pinata"""
    print("upload_profile_image endpoint called")
    print("FILES in request:", request.FILES)
    print("POST data:", request.POST)

    try:
        # Get the image file from the request
        image_file = request.FILES.get('image')
        if not image_file:
            print("No image file found in request")
            return JsonResponse({'success': False, 'error': 'No image file provided'}, status=400)

        print(f"Image file received: {image_file.name}, Size: {image_file.size}, Type: {image_file.content_type}")

        # Validate the image
        is_valid, error_message = validate_image(image_file)
        if not is_valid:
            return JsonResponse({'success': False, 'error': error_message}, status=400)

        # Get the user's profile
        try:
            profile = request.user.profile
        except UserProfile.DoesNotExist:
            # Create a profile if it doesn't exist
            profile = UserProfile.objects.create(user=request.user)

        # If there's an existing profile image on IPFS, delete it first
        if profile.profile_image and 'ipfs' in profile.profile_image:
            delete_from_ipfs(profile.profile_image)

        # Optimize the image
        optimized_image = optimize_image(image_file)

        # Upload to IPFS
        success, result = upload_to_ipfs(optimized_image)
        if success:
            # Update the profile with the IPFS URL
            profile.profile_image = result
            profile.save()

            # Verify the profile was updated correctly
            fresh_profile = UserProfile.objects.get(pk=profile.pk)
            print(f"Profile updated with image URL: {fresh_profile.profile_image}")

            # Return the IPFS URL
            return JsonResponse({
                'success': True,
                'url': result,
                'message': 'Image uploaded to IPFS and profile updated successfully'
            })
        else:
            return JsonResponse({'success': False, 'error': f'Failed to upload to IPFS: {result}'}, status=500)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# Create your views here.
def index(request):
    # Show landing page for non-authenticated users
    if not request.user.is_authenticated:
        return render(request, 'vibezin/landing.html')

    # Show vibes feed for authenticated users
    vibes = Vibe.objects.all().order_by('-created_at')
    context = {
        'vibes': vibes,
        'title': 'Your Vibe Feed'
    }
    return render(request, 'vibezin/index.html', context)

@login_required
def add_vibe(request):
    if request.method == 'POST':
        form = VibeForm(request.POST)
        if form.is_valid():
            vibe = form.save(commit=False)
            vibe.user = request.user
            # The slug will be automatically generated in the save method
            vibe.save()

            # Create the vibe directory
            ensure_vibe_directory_exists(vibe.slug)

            # Create initial content using AI if the user has an API key
            if hasattr(request.user, 'profile') and request.user.profile.chatgpt_api_key:
                # The content will be created when the vibe directory is accessed
                get_vibe_content(vibe)

            # Redirect to the new vibe's detail page using the slug
            return redirect('vibezin:vibe_detail_by_slug', vibe_slug=vibe.slug)
    else:
        form = VibeForm()

    context = {
        'form': form,
        'title': 'Add New Vibe'
    }
    return render(request, 'vibezin/add_vibe.html', context)

def vibe_detail(request, vibe_id):
    """View a vibe by its ID (for backward compatibility)"""
    vibe = get_object_or_404(Vibe, pk=vibe_id)
    # Redirect to the slug-based URL if available
    if vibe.slug:
        return redirect('vibezin:vibe_detail_by_slug', vibe_slug=vibe.slug)

    # If we don't have a slug, ensure the vibe has a directory
    # This should not happen with new vibes, but might with legacy data
    if not vibe.slug:
        # We should generate a slug for this vibe
        vibe.save()  # This will trigger the save method which generates a slug
        return redirect('vibezin:vibe_detail_by_slug', vibe_slug=vibe.slug)

    # Fallback rendering (should not be reached with proper data)
    context = {
        'vibe': vibe,
        'title': vibe.title
    }
    return render(request, 'vibezin/vibe_detail.html', context)

def vibe_detail_by_slug(request, vibe_slug):
    """View a vibe by its slug"""
    vibe = get_object_or_404(Vibe, slug=vibe_slug)

    # Ensure the vibe directory exists
    ensure_vibe_directory_exists(vibe.slug)

    # Get the vibe content from the directory
    content_result = get_vibe_content(vibe)
    vibe_content = content_result.get('content', {}) if content_result.get('success', False) else {}

    # Check if the vibe has custom HTML, CSS, or JS files
    from .file_utils import VibeFileManager
    file_manager = VibeFileManager(vibe)
    files = file_manager.list_files()

    # Look for custom HTML file (index.html or vibe.html)
    custom_html = None
    custom_css = None
    custom_js = None

    for file in files:
        if file['name'] in ['index.html', 'vibe.html']:
            custom_html = file_manager.read_file(file['name'])
            if custom_html.get('success', False):
                custom_html = custom_html.get('content', '')
        elif file['name'].endswith('.css'):
            custom_css = file_manager.read_file(file['name'])
            if custom_css.get('success', False):
                custom_css = custom_css.get('content', '')
        elif file['name'].endswith('.js'):
            custom_js = file_manager.read_file(file['name'])
            if custom_js.get('success', False):
                custom_js = custom_js.get('content', '')

    # If we have custom HTML, use it instead of the template
    # Check if we're in the AI builder preview mode
    is_preview = request.GET.get('preview', 'false').lower() == 'true'

    # ALWAYS use custom HTML if it exists, regardless of the flag
    # This ensures the preview always shows the custom HTML
    if custom_html:
        from django.http import HttpResponse

        # Log for debugging
        print(f"Using custom HTML for vibe: {vibe.slug}, has_custom_html: {vibe.has_custom_html}, is_preview: {is_preview}")

        # Replace placeholders in the HTML with actual content
        html = custom_html

        # Add the custom CSS if available
        if custom_css:
            if '<style>' not in html:
                html = html.replace('</head>', f'<style>{custom_css}</style></head>')
            elif '</head>' not in html:
                # If there's no </head> tag, add the style at the beginning
                html = f'<style>{custom_css}</style>\n{html}'

        # Add the custom JS if available
        if custom_js:
            if '<script>' not in html:
                if '</body>' in html:
                    html = html.replace('</body>', f'<script>{custom_js}</script></body>')
                else:
                    # If there's no </body> tag, add the script at the end
                    html = f'{html}\n<script>{custom_js}</script>'

        # If the vibe doesn't have the custom HTML flag set,
        # set it now to ensure future views work correctly
        if not vibe.has_custom_html:
            vibe.has_custom_html = True
            if custom_css:
                vibe.has_custom_css = True
            if custom_js:
                vibe.has_custom_js = True
            vibe.save()
            print(f"Updated custom flags for vibe: {vibe.slug} - HTML: {vibe.has_custom_html}, CSS: {vibe.has_custom_css}, JS: {vibe.has_custom_js}")

        return HttpResponse(html)

    # Otherwise, use the standard template
    context = {
        'vibe': vibe,
        'title': vibe.title,
        'vibe_content': vibe_content,
        'ai_generated': vibe_content.get('ai_generated', False),
        'custom_css': custom_css if vibe.has_custom_css else None,
        'custom_js': custom_js if vibe.has_custom_js else None
    }
    return render(request, 'vibezin/vibe_detail.html', context)

@login_required
def profile(request):
    """View for the current user's profile"""
    # Check if user has a profile, create one if not
    try:
        user_profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create a profile for this user
        user_profile = UserProfile.objects.create(user=request.user)
        messages.info(request, "We've created a new profile for you. Please update your information.")

    user_vibes = Vibe.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'profile': user_profile,
        'vibes': user_vibes,
        'title': f"{request.user.username}'s Profile",
        'is_owner': True
    }
    return render(request, 'vibezin/profile.html', context)

def user_profile(request, username):
    """View for any user's profile"""
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        raise Http404("User does not exist")

    # If user is trying to access their own profile, redirect to the profile view
    # This ensures all profile edits go through the proper edit_profile view
    if request.user.is_authenticated and request.user.username == username:
        return redirect('vibezin:profile')

    # Check if user has a profile, create one if not
    try:
        user_profile = user.profile
    except UserProfile.DoesNotExist:
        # Create a profile for this user
        user_profile = UserProfile.objects.create(user=user)
        if request.user == user:
            messages.info(request, "We've created a new profile for you. Please update your information.")

    user_vibes = Vibe.objects.filter(user=user).order_by('-created_at')
    context = {
        'profile': user_profile,
        'vibes': user_vibes,
        'title': f"{user.username}'s Profile",
        'is_owner': request.user == user if request.user.is_authenticated else False
    }
    return render(request, 'vibezin/profile.html', context)

@login_required
def edit_profile(request):
    """View for editing the current user's profile"""
    # Check if user has a profile, create one if not
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        # Create a profile for this user
        profile = UserProfile.objects.create(user=request.user)
        messages.info(request, "We've created a new profile for you. Please update your information.")

    # Handle profile image deletion if requested
    if request.method == 'POST' and ('delete_profile_image' in request.POST or
                                     (request.POST.get('profile_image', '') == '' and profile.profile_image)):
        old_image_url = profile.profile_image

        if old_image_url:
            print(f"Detected profile image deletion. Old URL: {old_image_url}")

            # Clear the profile image URL first to ensure it's saved
            profile.profile_image = ''
            profile.save()

            # Check if it's an IPFS URL
            if 'ipfs' in old_image_url:
                # Delete from Pinata
                print(f"Attempting to delete image from IPFS: {old_image_url}")
                success, message = delete_from_ipfs(old_image_url)
                if success:
                    print("Successfully deleted from IPFS")
                    messages.success(request, "Profile image deleted successfully from IPFS.")
                else:
                    print(f"Failed to delete from IPFS: {message}")
                    messages.warning(request, f"Image deleted from profile but there was an issue removing it from IPFS: {message}")
            else:
                messages.success(request, "Profile image removed successfully.")

            # Refresh the profile from the database to ensure we have the latest state
            profile = UserProfile.objects.get(pk=profile.pk)

            # If this was a dedicated delete request (not part of a form submission), redirect
            if 'delete_profile_image' in request.POST:
                return redirect('vibezin:edit_profile')

    # Initialize forms
    username_form = UsernameForm(instance=request.user, user=request.user)
    profile_form = ProfileForm(instance=profile)

    if request.method == 'POST':
        # Debug: Print all POST data
        print("POST data:", request.POST)

        # Handle username form
        if 'username' in request.POST and not 'bio' in request.POST:
            username_form = UsernameForm(request.POST, instance=request.user, user=request.user)
            if username_form.is_valid():
                username_form.save()
                messages.success(request, "Username updated successfully!")
                # Redirect to the new profile URL with the updated username
                return redirect('vibezin:profile')
            else:
                messages.error(request, "There was an error updating your username.")

        # Handle profile form submission (including social links and custom code)
        else:
            # Check if the profile image field is empty in the POST data
            post_data = request.POST.copy()  # Create a mutable copy of POST data

            # First check if we have a backup URL from the JavaScript
            backup_url = post_data.get('profile_image_backup')
            if backup_url:
                print(f"Found backup profile image URL: {backup_url}")
                post_data['profile_image'] = backup_url

            # If no backup but the field is empty and we have a URL in the database, preserve it
            elif not post_data.get('profile_image') and profile.profile_image:
                print(f"Empty profile_image in form submission, but database has: {profile.profile_image}")
                print("Preserving existing profile image URL in form data")
                post_data['profile_image'] = profile.profile_image

            profile_form = ProfileForm(post_data, request.FILES, instance=profile)
            if profile_form.is_valid():
                # Get the current profile image URL before saving the form
                current_profile_image = profile.profile_image
                print(f"Current profile image URL before form save: {current_profile_image}")

                # Save the form
                profile = profile_form.save()

                # Log the profile image URL for debugging
                print(f"Profile saved with image URL: {profile.profile_image}")

                # Double-check: If the profile image URL was still lost during form save, restore it
                if current_profile_image and not profile.profile_image and 'ipfs' in current_profile_image:
                    print(f"Profile image URL was lost during form save. Restoring: {current_profile_image}")
                    profile.profile_image = current_profile_image
                    profile.save()

                # Verify the profile was saved correctly
                fresh_profile = UserProfile.objects.get(pk=profile.pk)
                print("Profile after save (from DB):", {
                    'bio': fresh_profile.bio,
                    'profile_image': fresh_profile.profile_image,
                    'background_image': fresh_profile.background_image,
                    'theme': fresh_profile.theme,
                    'social_links': fresh_profile.social_links,
                })

                # Add debug information to confirm what was saved
                saved_fields = {
                    'bio': profile.bio[:50] + '...' if len(profile.bio) > 50 else profile.bio,
                    'profile_image': profile.profile_image,
                    'background_image': profile.background_image,
                    'theme': profile.theme,
                    'social_links': profile.social_links,
                }
                if request.user.is_staff:
                    saved_fields['custom_css'] = f"{len(profile.custom_css)} characters" if profile.custom_css else "None"
                    saved_fields['custom_html'] = f"{len(profile.custom_html)} characters" if profile.custom_html else "None"

                messages.success(request, "Profile updated successfully!")
                return redirect('vibezin:profile')
            else:
                messages.error(request, f"There was an error updating your profile: {profile_form.errors}")
                # Re-render the form with errors

    # Create forms for GET request
    username_form = UsernameForm(instance=request.user, user=request.user)
    profile_form = ProfileForm(instance=profile)

    # Ensure the profile image URL is properly populated in the form
    if profile.profile_image:
        print(f"Initializing form with profile_image={profile.profile_image}")
        profile_form.initial['profile_image'] = profile.profile_image

    context = {
        'profile': profile,
        'username_form': username_form,
        'profile_form': profile_form,
        'title': 'Edit Your Profile',
        'themes': ['default', 'dark', 'neon', 'retro', 'minimal']
    }
    return render(request, 'vibezin/edit_profile.html', context)


def debug_context(request):
    """Debug view to display all context variables"""
    # Get all context variables
    from allauth.socialaccount.models import SocialApp

    # Check if social apps are configured
    social_apps = SocialApp.objects.all()
    social_apps_list = [
        {
            'name': app.name,
            'provider': app.provider,
            'client_id': app.client_id[:10] + '...' if app.client_id else 'None',
            'sites': [site.domain for site in app.sites.all()]
        }
        for app in social_apps
    ]

    context = {
        'socialaccount_providers': social_apps.exists(),
        'debug_context': {
            'social_apps': social_apps_list,
            'social_apps_count': social_apps.count(),
            'user': request.user.username if request.user.is_authenticated else 'Anonymous',
            'request_path': request.path,
            'request_method': request.method,
        }
    }
    return render(request, 'vibezin/debug.html', context)
