from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    message = 'Admin access required.'
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)

class IsOwnerOrAdmin(BasePermission):
    message = 'You do not have permission.'
    def has_object_permission(self, request, view, obj):
        if request.user.is_admin: return True
        owner = getattr(obj, 'user', None) or getattr(obj, 'created_by', None)
        return owner == request.user
