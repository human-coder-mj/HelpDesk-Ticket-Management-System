"""
URL configuration for user_auth app
Authentication endpoints for session-based auth
"""
from django.urls import path
from . import views

app_name = 'user_auth'

urlpatterns = [
    # Authentication endpoints
    path('login/', views.login_user_view, name='login'),
    path('logout/', views.logout_user_view, name='logout'),
]