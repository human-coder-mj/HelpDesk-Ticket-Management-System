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
        
        self.admin_data = {
            'username': 'testadmin',
            'email': 'admin@test.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'Admin'
        }
        
        # Create users
        self.user = User.objects.create_user(**self.user_data)
        self.agent = User.objects.create_user(**self.agent_data)
        self.admin = User.objects.create_user(**self.admin_data)
        
        # Create profiles
        self.user_profile = UserProfile.objects.create(
            user=self.user,
            role=UserProfile.USER,
            phone='123-456-7890',
            department='IT'
        )
        
        self.agent_profile = UserProfile.objects.create(
            user=self.agent,
            role=UserProfile.AGENT,
            phone='123-456-7891',
            department='Support'
        )
        
        self.admin_profile = UserProfile.objects.create(
            user=self.admin,
            role=UserProfile.ADMIN,
            phone='123-456-7892',
            department='Administration'
        )
    
    def test_csrf_token_endpoint(self):
        """Test CSRF token retrieval"""
        url = reverse('user_auth:csrf_token')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('csrf_token', response.data)
        self.assertIsNotNone(response.data['csrf_token'])
    
    def test_session_status_anonymous(self):
        """Test session status for anonymous user"""
        url = reverse('user_auth:session_status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['authenticated'], False)
        self.assertIsNone(response.data['user'])
        self.assertIsNone(response.data['session_key'])
    
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
        
        # Check user data
        user_data = response.data['user']
        self.assertEqual(user_data['username'], self.user_data['username'])
        self.assertEqual(user_data['email'], self.user_data['email'])
        self.assertEqual(user_data['profile']['role'], UserProfile.USER)
    
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
    
    def test_current_user_authenticated(self):
        """Test current user endpoint when authenticated"""
        # Login first
        self.client.force_authenticate(user=self.user)

        url = reverse('user_auth:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], self.user_data['username'])

    def test_current_user_unauthenticated(self):
        """Test current user endpoint when not authenticated"""
        url = reverse('user_auth:current_user')
        response = self.client.get(url)

        # DRF returns 403 for permission denied (IsAuthenticated)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

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

    def test_session_status_authenticated(self):
        """Test session status when authenticated"""
        # Login first
        self.client.force_authenticate(user=self.user)

        url = reverse('user_auth:session_status')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['authenticated'], True)
        self.assertIsNotNone(response.data['user'])
        self.assertEqual(response.data['user']['username'], self.user_data['username'])

    def test_validate_session_authenticated(self):
        """Test session validation when authenticated"""
        # Login first
        self.client.force_authenticate(user=self.user)

        url = reverse('user_auth:validate_session')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['valid'], True)
        self.assertIn('user', response.data)
        self.assertIn('csrf_token', response.data)

    def test_validate_session_unauthenticated(self):
        """Test session validation when not authenticated"""
        url = reverse('user_auth:validate_session')
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['valid'], False)

    def test_agent_role_in_session_data(self):
        """Test that agent role is correctly returned in session data"""
        # Login as agent
        self.client.force_authenticate(user=self.agent)

        url = reverse('user_auth:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['profile']['role'], UserProfile.AGENT)
        self.assertEqual(response.data['user']['profile']['department'], 'Support')

    def test_admin_role_in_session_data(self):
        """Test that admin role is correctly returned in session data"""
        # Login as admin
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('user_auth:current_user')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['profile']['role'], UserProfile.ADMIN)
        self.assertEqual(response.data['user']['profile']['department'], 'Administration')


if __name__ == '__main__':
    import unittest
    unittest.main()