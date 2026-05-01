from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, VerifyEmailView, ResendOTPView,
    LoginView, LogoutView,
    ProfileView, ChangePasswordView,
    ClassmatesView,
    UserListView, UserDetailView,
)

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────────
    path('register/',            RegisterView.as_view(),     name='auth-register'),
    path('verify-email/',        VerifyEmailView.as_view(),  name='auth-verify-email'),
    path('resend-otp/',          ResendOTPView.as_view(),    name='auth-resend-otp'),
    path('login/',               LoginView.as_view(),        name='auth-login'),
    path('logout/',              LogoutView.as_view(),       name='auth-logout'),
    path('token/refresh/',       TokenRefreshView.as_view(), name='token-refresh'),

    # ── Profile ───────────────────────────────────────────────
    path('profile/',             ProfileView.as_view(),         name='auth-profile'),
    path('change-password/',     ChangePasswordView.as_view(),  name='change-password'),

    # ── Students ──────────────────────────────────────────────
    path('classmates/',          ClassmatesView.as_view(),      name='classmates'),

    # ── Admin ─────────────────────────────────────────────────
    path('users/',               UserListView.as_view(),        name='user-list'),
    path('users/<int:user_id>/', UserDetailView.as_view(),      name='user-detail'),
]
