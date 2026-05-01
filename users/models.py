"""
users/models.py
================
Custom User model with:
- University Roll Number (SU72-BSSEM-F25-017 format) as login identifier
- Email for verification only
- Email verification via OTP code
- Roles: student | admin
- Department: SE | CS
"""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db  import models
from django.utils import timezone
import random, string


def generate_otp():
    """Generate a 6-digit numeric OTP."""
    return ''.join(random.choices(string.digits, k=6))


class UserManager(BaseUserManager):

    def create_user(self, roll_number, name, email, password=None, **extra_fields):
        if not roll_number: raise ValueError('Roll number is required.')
        if not email:       raise ValueError('Email is required.')
        if not name:        raise ValueError('Name is required.')

        email       = self.normalize_email(email)
        roll_number = roll_number.upper().strip()
        extra_fields.setdefault('role', User.Role.STUDENT)

        user = self.model(
            roll_number=roll_number,
            email=email,
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, roll_number, name, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff',      True)
        extra_fields.setdefault('is_superuser',  True)
        extra_fields.setdefault('role',          User.Role.ADMIN)
        extra_fields.setdefault('is_verified',   True)  # admin doesn't need email verify
        return self.create_user(roll_number, name, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    University student/admin user.

    Login identifier: roll_number  (e.g. SU72-BSSEM-F25-017)
    Email:            used for verification code only
    """

    class Role(models.TextChoices):
        STUDENT = 'student', 'Student'
        ADMIN   = 'admin',   'Admin'

    class Department(models.TextChoices):
        SE   = 'SE', 'Software Engineering'
        CS   = 'CS', 'Computer Science'

    # ── Core fields ──────────────────────────────────────────────────────────
    roll_number  = models.CharField(
        max_length=30,
        unique=True,
        help_text='University Roll Number e.g. SU72-BSSEM-F25-017',
    )
    name         = models.CharField(max_length=150)
    email        = models.EmailField(
        unique=True,
        help_text='Used for verification code only.',
    )

    # ── Role & Department ─────────────────────────────────────────────────────
    role         = models.CharField(max_length=10, choices=Role.choices, default=Role.STUDENT)
    department   = models.CharField(
        max_length=2,
        choices=Department.choices,
        blank=True,
        default='',
    )

    # ── Email Verification ───────────────────────────────────────────────────
    is_verified      = models.BooleanField(
        default=False,
        help_text='True after email OTP is confirmed.',
    )
    otp_code         = models.CharField(max_length=6, blank=True, default='')
    otp_created_at   = models.DateTimeField(null=True, blank=True)

    # ── Django internals ──────────────────────────────────────────────────────
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    objects = UserManager()

    # Roll number is the login field
    USERNAME_FIELD  = 'roll_number'
    REQUIRED_FIELDS = ['name', 'email']

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.roll_number} — {self.name}'

    # ── Helpers ───────────────────────────────────────────────────────────────

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    def generate_otp(self):
        """Create a fresh OTP and save it."""
        self.otp_code       = generate_otp()
        self.otp_created_at = timezone.now()
        self.save(update_fields=['otp_code', 'otp_created_at'])
        return self.otp_code

    def verify_otp(self, code):
        """
        Returns True if code matches and is not expired (10 min window).
        """
        from django.conf import settings
        expiry_minutes = getattr(settings, 'EMAIL_VERIFICATION_EXPIRY_MINUTES', 10)

        if not self.otp_code or not self.otp_created_at:
            return False
        if self.otp_code != code.strip():
            return False

        age = (timezone.now() - self.otp_created_at).total_seconds() / 60
        return age <= expiry_minutes

    def clear_otp(self):
        self.otp_code       = ''
        self.otp_created_at = None
        self.save(update_fields=['otp_code', 'otp_created_at'])


class EmailVerification(models.Model):
    """
    Tracks email verification requests.
    Separate model for audit trail.
    """
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verifications')
    email      = models.EmailField()
    otp_code   = models.CharField(max_length=6)
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    used_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.roll_number} — {self.otp_code} — {"used" if self.is_used else "pending"}'
