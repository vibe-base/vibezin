from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Vibe, UserProfile
from .forms import VibeForm, UsernameForm

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

    if request.method == 'POST':
        # Handle username form
        username_form = UsernameForm(request.POST, instance=request.user, user=request.user)
        if 'username' in request.POST:
            if username_form.is_valid():
                username_form.save()
                messages.success(request, "Username updated successfully!")
                # Redirect to the new profile URL with the updated username
                return redirect('vibezin:profile')
            else:
                messages.error(request, "There was an error updating your username.")

        # Handle profile form submission
        profile.bio = request.POST.get('bio', '')
        profile.profile_image = request.POST.get('profile_image', '')
        profile.background_image = request.POST.get('background_image', '')
        profile.theme = request.POST.get('theme', 'default')

        # Handle custom CSS and HTML if user has permission
        if request.user.is_staff:  # Only staff can use custom CSS/HTML for security
            profile.custom_css = request.POST.get('custom_css', '')
            profile.custom_html = request.POST.get('custom_html', '')

        # Handle social links
        social_links = {}
        for key in ['twitter', 'instagram', 'github', 'linkedin', 'website']:
            if request.POST.get(f'social_{key}'):
                social_links[key] = request.POST.get(f'social_{key}')

        profile.social_links = social_links
        profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect('vibezin:profile')

    # Create forms for GET request
    username_form = UsernameForm(instance=request.user, user=request.user)

    context = {
        'profile': request.user.profile,
        'username_form': username_form,
        'title': 'Edit Your Profile',
        'themes': ['default', 'dark', 'neon', 'retro', 'minimal']
    }
    return render(request, 'vibezin/edit_profile.html', context)
