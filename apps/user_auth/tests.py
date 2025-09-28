"""
Tests for user authentication endpoints
Tests session-based authentication, login, logout, and permissions
"""
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from apps.users.models import UserProfile


class AuthenticationAPITestCase(APITestCase):
    """Test case for authentication API endpoints"""

    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test users with different roles
        self.user_data = {
            'username': 'testuser',
            'email': 'user@test.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        self.agent_data = {
            'username': 'testagent',
            'email': 'agent@test.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Agent'
        }
        
        # Create users
        self.user = User.objects.create_user(**self.user_data)
        self.agent = User.objects.create_user(**self.agent_data)
        
        # Create profiles
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            first_name='Test',
            last_name='User',
            role=UserProfile.USER,
            phone='123-456-7890',
            department='IT'
        )
        
        self.agent_profile = UserProfile.objects.create(
            user=self.agent,
            first_name='Test',
            last_name='Agent',
            role=UserProfile.AGENT,
            phone='123-456-7891',
            department='Support'
        )
    
    def test_login_success(self):
        """Test successful user login"""
        url = reverse('user_auth:login')
        data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Login successful')
        self.assertIn('user', response.data)
        self.assertIn('session_key', response.data)
        self.assertIn('csrf_token', response.data)
        
        # Check user data (now profile data)
        user_data = response.data['user']
        self.assertEqual(user_data['first_name'], 'Test')
        self.assertEqual(user_data['role'], UserProfile.USER)
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        url = reverse('user_auth:login')
        data = {
            'username': self.user_data['username'],
            'password': 'wrongpassword'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('non_field_errors', response.data)
    
    def test_login_missing_fields(self):
        """Test login with missing fields"""
        url = reverse('user_auth:login')
        data = {
            'username': self.user_data['username']
            # Missing password
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_logout_authenticated(self):
        """Test logout when authenticated"""
        # Login first
        self.client.force_authenticate(user=self.user)

        url = reverse('user_auth:logout')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logout successful')

    def test_logout_unauthenticated(self):
        """Test logout when not authenticated"""
        url = reverse('user_auth:logout')
        response = self.client.post(url)

        # DRF returns 403 for permission denied (IsAuthenticated)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_agent_role_login(self):
        """Test that agent role login works correctly"""
        url = reverse('user_auth:login')
        data = {
            'username': self.agent_data['username'],
            'password': self.agent_data['password']
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['role'], UserProfile.AGENT)
        self.assertEqual(response.data['user']['department'], 'Support')

    def test_login_user_without_profile(self):
        """Test login for user without profile returns 404"""
        # Create user without profile
        User.objects.create_user(
            username='noprofile',
            email='noprofile@test.com',
            password='testpass123'
        )
        
        url = reverse('user_auth:login')
        data = {
            'username': 'noprofile',
            'password': 'testpass123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], 'User profile not found')


if __name__ == '__main__':
    import unittest
    unittest.main()