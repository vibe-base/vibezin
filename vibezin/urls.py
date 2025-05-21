from django.urls import path
from . import views

app_name = 'vibezin'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_vibe, name='add_vibe'),
    path('vibe/<str:vibe_slug>/', views.vibe_detail_by_slug, name='vibe_detail_by_slug'),
    path('vibe/id/<int:vibe_id>/', views.vibe_detail, name='vibe_detail'),  # Keep for backward compatibility
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/upload-image/', views.upload_profile_image, name='upload_profile_image'),
    path('user/<str:username>/', views.user_profile, name='user_profile'),
]
