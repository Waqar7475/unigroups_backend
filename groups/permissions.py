"""
groups/permissions.py
======================
Group-specific DRF permission classes.
"""
from rest_framework.permissions import BasePermission

from .models import GroupMember


class IsGroupLeader(BasePermission):
    """
    Object-level permission: grants access only to the group's leader.
    The view must pass the `group` instance to check_object_permissions.
    Admins bypass this check.
    """
    message = 'Only the group leader can perform this action.'

    def has_object_permission(self, request, view, obj):
        # obj is a Group instance
        if request.user.is_admin:
            return True
        return GroupMember.objects.filter(
            group=obj,
            user=request.user,
            role=GroupMember.Role.LEADER,
        ).exists()


class IsGroupMember(BasePermission):
    """Allows access only to current members of the group."""
    message = 'You must be a member of this group to perform this action.'

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        return GroupMember.objects.filter(group=obj, user=request.user).exists()


class IsLeaderOrAdmin(BasePermission):
    """
    Checks if the authenticated user is either:
    - the leader of the group identified by `group_id` in request.data, OR
    - an application admin.
    Used for request-level checks (not object-level).
    """
    message = 'Only the group leader or an admin can perform this action.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_admin:
            return True

        # For views that pass group_id in the request body
        group_id = request.data.get('group_id')
        if group_id:
            return GroupMember.objects.filter(
                group_id=group_id,
                user=request.user,
                role=GroupMember.Role.LEADER,
            ).exists()

        return False
