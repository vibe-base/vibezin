from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseForbidden
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.conf import settings
from .models import Vibe, UserProfile
from .forms import VibeForm, UsernameForm, ProfileForm
from .utils import validate_image, optimize_image, upload_to_ipfs, delete_from_ipfs

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
            vibe.save()
            return redirect(reverse('vibezin:index'))
    else:
        form = VibeForm()

    context = {
        'form': form,
        'title': 'Add New Vibe'
    }
    return render(request, 'vibezin/add_vibe.html', context)

def vibe_detail(request, vibe_id):
    vibe = get_object_or_404(Vibe, pk=vibe_id)
    context = {
        'vibe': vibe,
        'title': vibe.title
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
            profile_form = ProfileForm(request.POST, request.FILES, instance=profile)
            if profile_form.is_valid():
                # Handle profile image upload to IPFS if provided
                profile_image_file = request.FILES.get('profile_image_file')
                ipfs_url = None  # Initialize the variable for later use

                if profile_image_file:
                    # Validate image
                    is_valid, error_message = validate_image(profile_image_file)
                    if not is_valid:
                        messages.error(request, error_message)
                    else:
                        # If there's an existing profile image on IPFS, delete it first
                        if profile.profile_image and 'ipfs' in profile.profile_image:
                            print(f"Deleting existing profile image from IPFS: {profile.profile_image}")
                            delete_from_ipfs(profile.profile_image)

                        # Optimize the image
                        print("Optimizing image for upload")
                        optimized_image = optimize_image(profile_image_file)

                        # Upload to IPFS
                        print("Uploading image to IPFS")
                        success, result = upload_to_ipfs(optimized_image)
                        if success:
                            # Store the IPFS URL for later use
                            ipfs_url = result
                            print(f"IPFS upload successful. URL: {ipfs_url}")

                            # Update the form's cleaned data with the new URL
                            profile_form.cleaned_data['profile_image'] = ipfs_url

                            messages.success(request, "Profile image uploaded to IPFS successfully!")
                        else:
                            messages.error(request, f"Failed to upload image to IPFS: {result}")
                            # Continue with form saving even if image upload failed

                # Get the profile data from the form but don't save yet
                profile = profile_form.save(commit=False)

                # If we have an IPFS URL from a successful upload, set it now
                if ipfs_url:
                    print(f"Setting profile image URL to: {ipfs_url}")
                    profile.profile_image = ipfs_url

                # Now save the profile with all updates
                profile.save()

                # Save many-to-many relationships if any
                profile_form.save_m2m()

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
