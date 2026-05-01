"""
users/serializers.py
=====================
Serializers for the updated User model (roll_number login + email OTP).
"""
import re
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


# ── Validators ────────────────────────────────────────────────────────────────

ROLL_NUMBER_PATTERN = re.compile(
    r'^SU\d{2}-[A-Z]{2,6}-[A-Z]\d{2}-\d{3,4}$',
    re.IGNORECASE
)

def validate_roll_number(value):
    """
    Validates Superior University roll number format.
    Examples:
      SU72-BSSEM-F25-017   ✓
      SU65-BSCS-F22-103    ✓
      SU72-BSSEM-F25-17    ✗  (too short)
      123456               ✗
    """
    cleaned = value.upper().strip()
    if not ROLL_NUMBER_PATTERN.match(cleaned):
        raise serializers.ValidationError(
            'Invalid roll number format. Expected: SU72-BSSEM-F25-017'
        )
    return cleaned


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    roll_number = serializers.CharField(validators=[validate_roll_number])
    password    = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2   = serializers.CharField(write_only=True, required=True, label='Confirm Password')

    class Meta:
        model  = User
        fields = [
            'roll_number', 'name', 'email',
            'password', 'password2',
            'department',
        ]
        extra_kwargs = {
            'department': {'required': True},
            'email':      {'required': True},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        return attrs

    def validate_email(self, value):
        cleaned = value.lower().strip()
        if User.objects.filter(email__iexact=cleaned).exists():
            raise serializers.ValidationError('This email is already registered.')
        return cleaned

    def validate_roll_number(self, value):
        cleaned = value.upper().strip()
        if User.objects.filter(roll_number__iexact=cleaned).exists():
            raise serializers.ValidationError('This roll number is already registered.')
        return cleaned

    def create(self, validated_data):
        validated_data.pop('password2')
        # New users start unverified
        validated_data['is_verified'] = False
        return User.objects.create_user(**validated_data)


# ── Login ─────────────────────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    """Login with roll_number + password."""
    roll_number = serializers.CharField()
    password    = serializers.CharField(write_only=True)

    def validate(self, attrs):
        roll_number = attrs.get('roll_number', '').upper().strip()
        password    = attrs.get('password')

        # authenticate() uses USERNAME_FIELD which is roll_number
        user = authenticate(
            request=self.context.get('request'),
            roll_number=roll_number,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                'Invalid roll number or password.'
            )
        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.')
        if not user.is_verified and not user.is_admin:
            raise serializers.ValidationError(
                'Please verify your email before logging in.',
                code='email_not_verified'
            )

        refresh = RefreshToken.for_user(user)
        return {
            'user':          user,
            'access_token':  str(refresh.access_token),
            'refresh_token': str(refresh),
        }


# ── Profile ───────────────────────────────────────────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    department_display = serializers.SerializerMethodField()

    class Meta:
        model  = User
        fields = [
            'id', 'roll_number', 'name', 'email',
            'role', 'department', 'department_display',
            'is_verified', 'created_at',
        ]
        read_only_fields = fields

    def get_department_display(self, obj):
        return obj.get_department_display() if obj.department else 'Not Set'


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['name']

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance


class AdminUpdateUserSerializer(serializers.ModelSerializer):
    """Admin can update name, department, role of any user."""
    class Meta:
        model  = User
        fields = ['name', 'department', 'role', 'is_verified']
        extra_kwargs = {f: {'required': False} for f in ['name', 'department', 'role', 'is_verified']}


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    def validate_old_password(self, value):
        if not self.context['request'].user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


# ── OTP ───────────────────────────────────────────────────────────────────────

class SendOTPSerializer(serializers.Serializer):
    """Request a new OTP — used during signup or resend."""
    roll_number = serializers.CharField()

    def validate_roll_number(self, value):
        cleaned = value.upper().strip()
        try:
            user = User.objects.get(roll_number=cleaned)
        except User.DoesNotExist:
            raise serializers.ValidationError('No account found with this roll number.')
        if user.is_verified:
            raise serializers.ValidationError('This account is already verified.')
        self.user = user
        return cleaned


class VerifyOTPSerializer(serializers.Serializer):
    """Verify the OTP code sent to email."""
    roll_number = serializers.CharField()
    otp_code    = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        roll_number = attrs.get('roll_number', '').upper().strip()
        otp_code    = attrs.get('otp_code', '').strip()

        try:
            user = User.objects.get(roll_number=roll_number)
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid roll number.')

        if user.is_verified:
            raise serializers.ValidationError('Account is already verified.')

        if not user.verify_otp(otp_code):
            raise serializers.ValidationError(
                'Invalid or expired verification code. Please request a new one.'
            )

        self.user = user
        return attrs
