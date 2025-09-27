from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import UserProfile


class ProfileCreateSerializer(serializers.ModelSerializer):
    """
    Nested serializer for profile creation during registration
    """
    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'role', 'phone', 'department')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': False, 'allow_blank': True},
            'role': {'default': UserProfile.USER},
            'phone': {'required': False, 'allow_blank': True},
            'department': {'required': False, 'allow_blank': True},
        }


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration with nested profile
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    profile = ProfileCreateSerializer()

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'profile')
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
        }

    def validate(self, attrs):
        """
        Validate password confirmation
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password and password confirmation do not match.")
        return attrs

    def create(self, validated_data):
        """
        Create user and profile using nested data
        """
        # Remove password_confirm and profile data
        validated_data.pop('password_confirm')
        profile_data = validated_data.pop('profile')

        # Create user
        user = User.objects.create_user(**validated_data)

        # Create profile with user relation
        UserProfile.objects.create(user=user, **profile_data)

        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details (read-only)
    """
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'date_joined', 'profile')

    def get_profile(self, obj):
        """
        Get user profile data
        """
        try:
            return ProfileSerializer(obj.profile).data
        except UserProfile.DoesNotExist:
            return None


class ProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    nameEmail = serializers.ReadOnlyField()
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = UserProfile
        fields = ('id', 'first_name', 'last_name', 'role', 'phone', 
                 'department', 'created_at', 'updated_at', 'nameEmail', 'full_name')
        read_only_fields = ('id', 'created_at', 'updated_at', 'nameEmail', 'full_name')


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_new_password(self, value):
        """
        Validate new password using Django's built-in validators
        """
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value


class UserSearchSerializer(serializers.ModelSerializer):
    """
    Serializer for user search results
    """
    nameEmail = serializers.ReadOnlyField(source='profile.nameEmail')
    role_display = serializers.ReadOnlyField(source='profile.get_role_display')

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'nameEmail', 'role_display')