# User URL patterns
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    register_user_view,
    delete_user_view,
    change_password_view,
    ProfileViewSet,
    UserViewSet
)

app_name = 'users'

# Create router for ViewSets
router = DefaultRouter()
router.register(r'profile', ProfileViewSet, basename='profile')
router.register(r'search', UserViewSet, basename='user-search')

urlpatterns = [
    # Authentication endpoints
    path('register/', register_user_view, name='register'),
    path('delete/', delete_user_view, name='delete-user'),
    path('change-password/', change_password_view, name='change-password'),

    # Include router URLs for ViewSets
    path('', include(router.urls)),
]