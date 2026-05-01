"""
users/views.py
==============
Auth + User Management views.

Routes (/api/auth/):
  POST register/             — signup (sends OTP email)
  POST verify-email/         — confirm OTP code
  POST resend-otp/           — resend OTP
  POST login/                — roll_number + password login
  POST logout/               — blacklist refresh token
  POST token/refresh/        — get new access token
  GET/PATCH profile/         — own profile
  POST change-password/      — own password
  GET  classmates/           — same dept students (student only)
  GET  users/                — list users (admin)
  GET/PATCH/DELETE users/<id>/ — manage user (admin)
"""
from django.utils    import timezone
from rest_framework  import status
from rest_framework.response import Response
from rest_framework.views    import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens     import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models      import User
from .serializers import (
    RegisterSerializer, LoginSerializer,
    UserProfileSerializer, UserUpdateSerializer,
    AdminUpdateUserSerializer, ChangePasswordSerializer,
    SendOTPSerializer, VerifyOTPSerializer,
)
from .permissions   import IsAdminUser
from .email_utils   import send_verification_email, send_welcome_email


# ── Registration & Verification ───────────────────────────────────────────────

class RegisterView(APIView):
    """
    POST /api/auth/register/
    Creates account (unverified) and sends OTP to email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)

        user     = s.save()
        otp_code = user.generate_otp()

        # Send verification email
        email_sent = send_verification_email(user, otp_code)

        return Response({
            'success':    True,
            'message':    f'Account created. Verification code sent to {user.email}',
            'roll_number': user.roll_number,
            'email_sent': email_sent,
            # In dev mode (console backend), show OTP in response
            'dev_otp':    otp_code if not email_sent else None,
        }, status=201)


class VerifyEmailView(APIView):
    """
    POST /api/auth/verify-email/
    Body: { "roll_number": "SU72-BSSEM-F25-017", "otp_code": "123456" }
    Verifies OTP and activates account. Returns JWT tokens on success.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = VerifyOTPSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)

        user             = s.user
        user.is_verified = True
        user.save(update_fields=['is_verified'])
        user.clear_otp()

        # Send welcome email
        send_welcome_email(user)

        # Auto-login after verification
        refresh = RefreshToken.for_user(user)

        return Response({
            'success':       True,
            'message':       f'Email verified! Welcome {user.name}.',
            'user':          UserProfileSerializer(user).data,
            'access_token':  str(refresh.access_token),
            'refresh_token': str(refresh),
        })


class ResendOTPView(APIView):
    """
    POST /api/auth/resend-otp/
    Body: { "roll_number": "SU72-BSSEM-F25-017" }
    Resends a fresh OTP to the user's email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = SendOTPSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)

        user     = s.user
        otp_code = user.generate_otp()
        email_sent = send_verification_email(user, otp_code)

        return Response({
            'success':    True,
            'message':    f'New verification code sent to {user.email}',
            'email_sent': email_sent,
            'dev_otp':    otp_code if not email_sent else None,
        })


# ── Login / Logout ────────────────────────────────────────────────────────────

class LoginView(APIView):
    """
    POST /api/auth/login/
    Body: { "roll_number": "SU72-BSSEM-F25-017", "password": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        s = LoginSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            # Check if error is about email not verified
            errors   = s.errors
            non_field = errors.get('non_field_errors', [])
            is_unverified = any(
                getattr(e, 'code', None) == 'email_not_verified'
                or 'verify your email' in str(e)
                for e in non_field
            )
            return Response({
                'success':      False,
                'errors':       errors,
                'unverified':   is_unverified,
            }, status=400)

        data = s.validated_data
        return Response({
            'success':       True,
            'message':       'Login successful.',
            'user':          UserProfileSerializer(data['user']).data,
            'access_token':  data['access_token'],
            'refresh_token': data['refresh_token'],
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        if not refresh_token:
            return Response({'success': False, 'message': 'Refresh token required.'}, status=400)
        try:
            RefreshToken(refresh_token).blacklist()
            return Response({'success': True, 'message': 'Logged out.'})
        except TokenError:
            return Response({'success': False, 'message': 'Invalid token.'}, status=400)


# ── Profile ───────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'success': True, 'user': UserProfileSerializer(request.user).data})

    def patch(self, request):
        s = UserUpdateSerializer(request.user, data=request.data, partial=True)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        s.save()
        return Response({'success': True, 'user': UserProfileSerializer(request.user).data})


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        s.save()
        return Response({'success': True, 'message': 'Password changed.'})


# ── Classmates ────────────────────────────────────────────────────────────────

class ClassmatesView(APIView):
    """GET /api/auth/classmates/ — students in same department."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.department:
            return Response({
                'success': False,
                'message': 'No department assigned. Contact admin.',
                'classmates': [],
            })
        classmates = User.objects.filter(
            department=user.department,
            role=User.Role.STUDENT,
            is_active=True,
        ).exclude(pk=user.pk)
        return Response({
            'success':            True,
            'department':         user.department,
            'department_display': user.get_department_display(),
            'count':              classmates.count(),
            'classmates':         UserProfileSerializer(classmates, many=True).data,
        })


# ── Admin: User Management ────────────────────────────────────────────────────

class UserListView(APIView):
    """GET /api/auth/users/?dept=SE&role=student"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        dept  = request.query_params.get('dept')
        role  = request.query_params.get('role')
        if dept: users = users.filter(department=dept)
        if role: users = users.filter(role=role)
        return Response({
            'success': True,
            'count':   users.count(),
            'users':   UserProfileSerializer(users, many=True).data,
        })


class UserDetailView(APIView):
    """GET / PATCH / DELETE /api/auth/users/<id>/"""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def _get(self, user_id):
        try:    return User.objects.get(pk=user_id)
        except: return None

    def get(self, request, user_id):
        u = self._get(user_id)
        if not u: return Response({'success': False, 'message': 'Not found.'}, status=404)
        return Response({'success': True, 'user': UserProfileSerializer(u).data})

    def patch(self, request, user_id):
        u = self._get(user_id)
        if not u: return Response({'success': False, 'message': 'Not found.'}, status=404)
        if u == request.user and request.data.get('role') == 'student':
            return Response({'success': False, 'message': 'Cannot remove your own admin role.'}, status=400)
        s = AdminUpdateUserSerializer(u, data=request.data, partial=True)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        s.save()
        return Response({'success': True, 'message': 'User updated.', 'user': UserProfileSerializer(u).data})

    def delete(self, request, user_id):
        u = self._get(user_id)
        if not u: return Response({'success': False, 'message': 'Not found.'}, status=404)
        if u == request.user:
            return Response({'success': False, 'message': 'Cannot delete yourself.'}, status=400)
        name = u.name
        u.delete()
        return Response({'success': True, 'message': f'{name} deleted.'})
