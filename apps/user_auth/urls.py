"""
URL configuration for user_auth app
Authentication endpoints for session-based auth
"""
from django.urls import path
from . import views

app_name = 'user_auth'

urlpatterns = [
    path('login/', views.LoginUserView.as_view(),  name='login'),
]