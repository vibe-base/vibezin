from django.urls import path
from . import views
from . import views_ai
from . import views_image

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

    # AI Builder URLs
    path('vibe/<str:vibe_slug>/ai/', views_ai.vibe_ai_builder, name='vibe_ai_builder'),
    path('vibe/<str:vibe_slug>/ai/message/', views_ai.vibe_ai_message, name='vibe_ai_message'),
    path('vibe/<str:vibe_slug>/ai/clear-conversation/', views_ai.vibe_ai_clear_conversation, name='vibe_ai_clear_conversation'),
    path('vibe/<str:vibe_slug>/ai/file/', views_ai.vibe_ai_file_operation, name='vibe_ai_file_operation'),
    path('vibe/<str:vibe_slug>/enable-custom-html/', views_ai.enable_custom_html, name='enable_custom_html'),

    # AI Image Generation URLs
    path('generate-image/', views_image.generate_image_view, name='generate_image'),
    path('vibe/<str:vibe_slug>/generate-image/', views_image.generate_image_view, name='vibe_generate_image'),
    path('my-images/', views_image.user_images, name='user_images'),
    path('doge-generator/', views_image.doge_generator, name='doge_generator'),

    # Debug URLs
    path('debug/', views.debug_context, name='debug_context'),
]
