from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import viewsets, permissions, status, parsers, filters
from rest_framework.response import Response
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.request import Request
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserProfile
from .serializers import (
    UserRegistrationSerializer,
    ProfileSerializer,
    ChangePasswordSerializer,
    UserSearchSerializer
)


@api_view(["POST"])
@permission_classes([permissions.AllowAny])
def register_user_view(request):
    """
    User registration endpoint
    Creates both User and UserProfile in a single transaction
    """
    serializer = UserRegistrationSerializer(data=request.data)

    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "detail": "User registered successfully. Please log in.",
                "user_id": user.id,
                "username": user.username
            },
            status=status.HTTP_201_CREATED
        )

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@permission_classes([permissions.IsAuthenticated])
def delete_user_view(request: Request) -> Response:
    """
    Delete the authenticated user's account
    This will also delete the associated profile due to CASCADE
    """
    try:
        user = request.user
        username = user.username
        user.delete()
        return Response(
            {"detail": f"User '{username}' has been deleted successfully"},
            status=status.HTTP_204_NO_CONTENT
        )
    except Exception as e:
        return Response(
            {"error": "An error occurred while deleting the user"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user profiles
    Users can only access and modify their own profile
    """
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.JSONParser, parsers.FormParser, parsers.MultiPartParser]

    def get_queryset(self):
        """
        Filter queryset to only show the authenticated user's profile
        """
        return UserProfile.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """
        Get the authenticated user's profile
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def update(self, request, *args, **kwargs):
        """
        Update the authenticated user's profile
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    def destroy(self, request, *args, **kwargs):
        """
        Delete the authenticated user's profile
        Note: This only deletes the profile, not the User account
        """
        try:
            profile = UserProfile.objects.get(user=request.user)
            profile.delete()
            return Response(
                {"detail": "Profile has been deleted successfully"},
                status=status.HTTP_204_NO_CONTENT
            )
        except UserProfile.DoesNotExist:
            return Response(
                {"error": "Profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='me')
    def get_own_profile(self, request):
        """
        Custom endpoint: GET /api/users/profile/me/
        Returns the authenticated user's profile
        """
        return self.retrieve(request)


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user search and listing
    Provides search functionality with nameEmail computed field
    """
    queryset = User.objects.select_related('profile').all()
    serializer_class = UserSearchSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'profile__first_name', 'profile__last_name']
    ordering_fields = ['username', 'email', 'date_joined']
    ordering = ['-date_joined']

    def get_queryset(self):
        """
        Filter users based on search parameters
        Supports searching by nameEmail computed field
        """
        queryset = User.objects.select_related('profile').all()
        
        # Search by nameEmail format: "FirstName LastName - Email"
        name_email_search = self.request.query_params.get('nameEmail', None)
        if name_email_search:
            queryset = queryset.filter(
                Q(profile__first_name__icontains=name_email_search) |
                Q(profile__last_name__icontains=name_email_search) |
                Q(email__icontains=name_email_search) |
                Q(username__icontains=name_email_search)
            )
        
        return queryset

    @action(detail=False, methods=['get'], url_path='search')
    def search_users(self, request):
        """
        Custom endpoint: GET /api/users/search/
        Advanced user search with nameEmail support
        """
        queryset = self.filter_queryset(self.get_queryset())
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request: Request) -> Response:
    """
    Change password endpoint for authenticated users
    Validates old password and enforces password security
    """
    user = request.user
    serializer = ChangePasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    old_password = serializer.validated_data.get("old_password")
    new_password = serializer.validated_data.get("new_password")

    # Check if new password is different from old password
    if new_password == old_password:
        return Response(
            {"error": "New password cannot be the same as the old password."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Verify old password
    if not user.check_password(old_password):
        return Response(
            {"error": "Incorrect old password."},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Set new password
    user.set_password(new_password)
    user.save()

    # Keep user logged in after password change
    update_session_auth_hash(request, user)

    return Response(
        {'detail': 'Your password has been successfully changed.'},
        status=status.HTTP_200_OK
    )