"""
Authentication serializers for user_auth app
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer



class LoginSerializer(TokenObtainPairSerializer):
    """
    Serializer for user login
    """
    login = serializers.CharField()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the original username field if it exists
        self.fields.pop('username', None)

    def validate(self, attrs):
        """
        Validate user credentials
        """
        login = attrs.get('login')
        password = attrs.get('password')
        
        if not login or not password:
            raise serializers.ValidationError(
                'Must include login (username or email) and password.'
            )
        
        # First try to authenticate with username
        user = authenticate(username=login, password=password)
        
        if user:
            user_obj = User.objects.get(username=login)

        if not user:
            try:
                # Find user by email
                user_obj = User.objects.get(email=login)
                # Authenticate using the found user's username
                user = authenticate(username=user_obj.username, password=password)
            except User.DoesNotExist:
                user = None
        
        
        if not user:
            raise serializers.ValidationError('Invalid login credentials.')
        
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        
        refresh = self.get_token(user)
        
        return {
            'user_obj' : user_obj,
            "tokens" : {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                }
            }



