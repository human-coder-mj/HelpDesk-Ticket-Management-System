"""
Authentication views for user_auth app
Handles session-based authentication, login, logout, and session management
"""
from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.request import Request
from apps.users.models import UserProfile
from apps.users.serializers import ProfileSerializer
from .serializers import (
    LoginSerializer,
)

#use rest of serializers in future use case


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def login_user_view(request: Request) -> Response:
    """
    User login endpoint with session-based authentication
    
    POST /api/auth/login/
    Body: {"username": "user123", "password": "password123"}
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Log the user in (creates session)
        login(request, user)
        
        try:
            profile = UserProfile.objects.get(user=user)
            profile_serializer = ProfileSerializer(profile)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "User profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        # Get CSRF token for frontend
        csrf_token = get_token(request)
        
        # Prepare response data
        response_data = {
            'message': 'Login successful',
            'user': profile_serializer.data,
            'session_key': request.session.session_key,
            'csrf_token': csrf_token
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@permission_classes([permissions.IsAuthenticated])
def logout_user_view(request: Request) -> Response:
    """
    User logout endpoint
    Clears session and logs out the user
    
    POST /api/auth/logout/
    """
    try:
        # Clear session data
        request.session.flush()

        # Log the user out
        logout(request)

        response_data = {
            'message': 'Logout successful'
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception:
        return Response(
            {'error': 'An error occurred during logout'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


