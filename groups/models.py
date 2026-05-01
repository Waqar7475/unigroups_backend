"""
groups/models.py
=================
Core data models for the group management system.
"""
from django.db   import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


class Group(models.Model):

    class Status(models.TextChoices):
        OPEN   = 'open',   'Open'
        LOCKED = 'locked', 'Locked'

    class Department(models.TextChoices):
        SE = 'SE', 'Software Engineering'
        CS = 'CS', 'Computer Science'

    # Basic info
    name        = models.CharField(max_length=200)
    department  = models.CharField(
        max_length=2,
        choices=Department.choices,
        default=Department.SE,
    )
    description = models.TextField(blank=True, default='')
    max_members = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(2), MaxValueValidator(20)],
    )

    # State
    status    = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    is_locked = models.BooleanField(default=False)

    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_groups',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'groups'
        ordering  = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_department_display()})'

    @property
    def member_count(self):
        return self.memberships.count()

    @property
    def slots_remaining(self):
        return max(0, self.max_members - self.member_count)

    @property
    def is_full(self):
        return self.member_count >= self.max_members

    def get_leader(self):
        membership = self.memberships.filter(role=GroupMember.Role.LEADER).first()
        return membership.user if membership else None

    def lock(self):
        self.is_locked = True
        self.status    = self.Status.LOCKED
        self.save(update_fields=['is_locked', 'status', 'updated_at'])

    def unlock(self):
        self.is_locked = False
        self.status    = self.Status.OPEN
        self.save(update_fields=['is_locked', 'status', 'updated_at'])


class GroupMember(models.Model):

    class Role(models.TextChoices):
        LEADER = 'leader', 'Leader'
        MEMBER = 'member', 'Member'

    group     = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user      = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='group_memberships',
    )
    role      = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table        = 'group_members'
        unique_together = [['group', 'user']]
        ordering        = ['joined_at']

    def __str__(self):
        return f'{self.user.name} → {self.group.name} [{self.role}]'


class JoinRequest(models.Model):

    class RequestStatus(models.TextChoices):
        PENDING  = 'pending',  'Pending'
        ACCEPTED = 'accepted', 'Accepted'
        REJECTED = 'rejected', 'Rejected'

    group       = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='join_requests')
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='join_requests',
    )
    status      = models.CharField(max_length=10, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    message     = models.TextField(blank=True, default='')
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviewed_requests',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table        = 'join_requests'
        unique_together = [['group', 'user']]
        ordering        = ['-created_at']

    def __str__(self):
        return f'{self.user.name} → {self.group.name} [{self.status}]'
