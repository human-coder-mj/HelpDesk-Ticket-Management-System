from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    '''
    User Profile Schema for HelpDesk System
    Extends Django's built-in User model with additional fields
    '''

    USER = 'user'
    AGENT = 'agent'
    ADMIN = 'admin'

    ROLE_CHOICES = [
        (USER, 'User'),
        (AGENT, 'Agent'),
        (ADMIN, 'Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=USER)
    phone = models.CharField(max_length=15, blank=True)
    department = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Profiile'
        verbose_name_plural = 'User Profiles'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.user.username} - {self.get_role_display()}'
    
    @property
    def nameEmail(self) -> str:
        """
        Computed property that returns 'FirstName LastName - Email'
        as specified in the requirements
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return f"{full_name} - {self.user.email}"

    @property
    def full_name(self) -> str:
        """
        Returns the full name of the user
        """
        return f"{self.first_name} {self.last_name}".strip()

    def is_user(self) -> bool:
        """Check if the user has 'user' role"""
        return self.role == self.USER

    def is_agent(self) -> bool:
        """Check if the user has 'agent' role"""
        return self.role == self.AGENT

    def is_admin(self) -> bool:
        """Check if the user has 'admin' role"""
        return self.role == self.ADMIN