from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Vibe, UserProfile
from .forms import VibeForm, UsernameForm, ProfileForm

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

    # Initialize forms
    username_form = UsernameForm(instance=request.user, user=request.user)
    profile_form = ProfileForm(instance=profile)

    if request.method == 'POST':
        # Debug: Print all POST data
        print("POST data:", request.POST)

        # Handle username form
        if 'username' in request.POST:
            username_form = UsernameForm(request.POST, instance=request.user, user=request.user)
            if username_form.is_valid():
                username_form.save()
                messages.success(request, "Username updated successfully!")
                # Redirect to the new profile URL with the updated username
                return redirect('vibezin:profile')
            else:
                messages.error(request, "There was an error updating your username.")

        # Handle profile form submission
        elif 'bio' in request.POST:
            profile_form = ProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()

                # Debug: Print profile after form save
                print("Profile after form save:", {
                    'bio': profile.bio,
                    'profile_image': profile.profile_image,
                    'background_image': profile.background_image,
                    'theme': profile.theme,
                })

                messages.success(request, "Profile information updated successfully!")
                return redirect('vibezin:edit_profile')
            else:
                messages.error(request, f"There was an error updating your profile: {profile_form.errors}")

        # Handle social links and custom code separately
        elif 'twitter' in request.POST or 'instagram' in request.POST or 'github' in request.POST or 'linkedin' in request.POST or 'website' in request.POST:
            # Process social links
            social_links = {}
            for platform in ['twitter', 'instagram', 'github', 'linkedin', 'website']:
                url = request.POST.get(platform, '').strip()
                if url:
                    social_links[platform] = url

            profile.social_links = social_links
            profile.save()
            messages.success(request, "Social links updated successfully!")
            return redirect('vibezin:edit_profile')

        # Handle custom CSS and HTML if user has permission
        elif request.user.is_staff and ('custom_css' in request.POST or 'custom_html' in request.POST):  # Only staff can use custom CSS/HTML for security
            profile.custom_css = request.POST.get('custom_css', '')
            profile.custom_html = request.POST.get('custom_html', '')
            profile.save()
            messages.success(request, "Custom code updated successfully!")
            return redirect('vibezin:edit_profile')

        # Handle social links
        social_links = {}
        for key in ['twitter', 'instagram', 'github', 'linkedin', 'website']:
            if request.POST.get(f'social_{key}'):
                social_links[key] = request.POST.get(f'social_{key}')

        profile.social_links = social_links

        # Debug: Print profile before saving
        print("Profile to save:", {
            'bio': profile.bio,
            'profile_image': profile.profile_image,
            'background_image': profile.background_image,
            'theme': profile.theme,
            'social_links': profile.social_links,
        })

        profile.save()

        # Debug: Verify profile was saved by fetching it again from the database
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

        messages.success(request, f"Profile updated successfully! Fields: {saved_fields}")
        return redirect('vibezin:profile')

    # Create forms for GET request
    username_form = UsernameForm(instance=request.user, user=request.user)
    profile_form = ProfileForm(instance=profile)

    context = {
        'profile': profile,
        'username_form': username_form,
        'profile_form': profile_form,
        'title': 'Edit Your Profile',
        'themes': ['default', 'dark', 'neon', 'retro', 'minimal']
    }
    return render(request, 'vibezin/edit_profile.html', context)
