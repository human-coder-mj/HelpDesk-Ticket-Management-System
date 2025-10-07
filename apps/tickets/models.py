"""
Ticket management models for HelpDesk system
Handles tickets, categories, priorities, statuses, comments
"""
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.crypto import get_random_string

class Ticket(models.Model):
    """
    Core ticket model for HelpDesk system
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
        ]

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]


    ticket_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique ticket identifier (auto-generated)"
    )

    title = models.CharField(max_length=200,
            help_text="Brief summary of the issue"
    )
    description = models.TextField()

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_tickets',
        help_text="User who created the ticket"
    )
    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets',
        limit_choices_to={'profile__role__in': ['AGENT', 'ADMIN']},
        help_text="Agent/Admin assigned to handle this ticket"
    )

    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text="Priority level of the ticket"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open',
        help_text="Current status of the ticket",
        db_index=True  # Index for faster filtering by status
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_id']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"#{self.ticket_id} - {self.title}"

    def save(self, *args, **kwargs):
        """Override save to set ticket_id and SLA times"""
        if not self.ticket_id:
            self.ticket_id = self.generate_ticket_id()

        super().save(*args, **kwargs)

        # Update resolved/closed timestamps
        if self.status == 'resolved' and not self.resolved_at:
            self.resolved_at = timezone.now()

        if self.status == 'closed' and not self.closed_at:
            self.closed_at = timezone.now()


    def generate_ticket_id(self):
        """Generate unique ticket ID"""

        # Format: TKT-YYYY-XXXXXX (e.g., TKT-2025-ABC123)
        year = datetime.now().year
        random_part = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
        ticket_id = f"TKT-{year}-{random_part}"

        # Ensure uniqueness
        while Ticket.objects.filter(ticket_id=ticket_id).exists():
            random_part = get_random_string(6, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            ticket_id = f"TKT-{year}-{random_part}"

        return ticket_id


    @property
    def time_to_resolution(self):
        """Time taken to resolve ticket"""
        if self.resolved_at:
            return self.resolved_at - self.created_at
        return None

    def assign_to_agent(self, agent, assigned_by=None):
        """Assign ticket to an agent"""
        if agent.profile.role in ['AGENT', 'ADMIN']:
            self.assigned_to = agent
            self.save()

            # Create comment about assignment
            Comment.objects.create(
                ticket=self,
                user=assigned_by or agent,
                comment_type='system',
                content=f"Ticket assigned to {agent.get_full_name() or agent.username}"
            )

            return True
        return False


class Comment(models.Model):
    """
    Comments and updates on tickets
    """
    COMMENT_TYPES = [
        ('comment', 'Comment'),
        ('system', 'System Update'),
        ('status_change', 'Status Change'),
        ('assignment', 'Assignment'),
        ('escalation', 'Escalation'),
    ]

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='comments',
        help_text="The ticket this comment belongs to"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ticket_comments',
        help_text="User who wrote the comment"
    )
    content = models.TextField(
        help_text="Comment text"
    )
    comment_type = models.CharField(max_length=20, choices=COMMENT_TYPES, default='comment')
    is_internal = models.BooleanField(
        default=False,
        help_text="Whether this comment is internal (visible only to staff) or public"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['comment_type']),
        ]

    def __str__(self):
        return f"Comment on {self.ticket.ticket_id} by {self.user.username}"