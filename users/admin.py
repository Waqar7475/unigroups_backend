from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, EmailVerification

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display   = ['roll_number', 'name', 'email', 'role', 'department', 'is_verified', 'is_active', 'created_at']
    list_filter    = ['role', 'department', 'is_verified', 'is_active']
    search_fields  = ['roll_number', 'email', 'name']
    ordering       = ['-created_at']
    fieldsets = (
        (None,           {'fields': ('roll_number', 'email', 'password')}),
        ('Personal',     {'fields': ('name',)}),
        ('Role & Dept',  {'fields': ('role', 'department')}),
        ('Verification', {'fields': ('is_verified', 'otp_code', 'otp_created_at')}),
        ('Permissions',  {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Timestamps',   {'fields': ('created_at', 'updated_at')}),
    )
    add_fieldsets = ((None, {
        'classes': ('wide',),
        'fields':  ('roll_number', 'name', 'email', 'password1', 'password2', 'role', 'department'),
    }),)
    readonly_fields = ['created_at', 'updated_at', 'otp_created_at']

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'email', 'otp_code', 'is_used', 'created_at']
    list_filter   = ['is_used']
    readonly_fields = ['created_at', 'used_at']
