from django.urls import path
from . import views

app_name = 'vibezin'

urlpatterns = [
    path('', views.index, name='index'),
    path('add/', views.add_vibe, name='add_vibe'),
    path('vibe/<int:vibe_id>/', views.vibe_detail, name='vibe_detail'),
]
