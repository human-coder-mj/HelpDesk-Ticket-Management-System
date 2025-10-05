"""
Authentication views for user_auth app
Handles session-based authentication, login, logout, and session management
"""
from rest_framework import response, status
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.user_profile.serializers import ProfileSerializer
from .serializers import LoginSerializer

#use rest of serializers in future use case


class LoginUserView(TokenObtainPairView):
    '''
        Authentication view to handle login request
    '''
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs) -> response.Response:
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            tokens = serializer.validated_data["tokens"]
            user_obj = serializer.validated_data["user_obj"]
            return response.Response(
                {
                    "message": "Login successful",
                    "profile": ProfileSerializer(user_obj).data,
                    "tokens": tokens
                },
                status=status.HTTP_200_OK
            )
        
        return response.Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


