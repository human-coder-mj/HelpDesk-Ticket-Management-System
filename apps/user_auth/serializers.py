"""
Authentication serializers for user_auth app
"""
from rest_framework import serializers
from django.contrib.auth import authenticate


class LoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """

    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, attrs):
        """
        Validate user credentials
        """
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            # Authenticate user
            user = authenticate(username=username, password=password)
            
            if user:
                if user.is_active:
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError("User account is disabled.")
            else:
                raise serializers.ValidationError("Invalid username or password.")
        else:
            raise serializers.ValidationError("Must include username and password.")
