"""
groups/urls.py
===============
All group routes under /api/groups/
"""
from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupDetailView,
    GroupUpdateView, GroupDeleteView,
    JoinRequestView, MyJoinRequestsView,
    AcceptRequestView, RejectRequestView,
    LockGroupView, UnlockGroupView,
    GroupMembersView, RemoveMemberView, AddMemberView,
    MyGroupsView,
)

urlpatterns = [
    # ── Group CRUD ────────────────────────────────────────
    path('',                          GroupListView.as_view(),    name='group-list'),
    path('create/',                   GroupCreateView.as_view(),  name='group-create'),
    path('<int:group_id>/',           GroupDetailView.as_view(),  name='group-detail'),
    path('<int:group_id>/update/',    GroupUpdateView.as_view(),  name='group-update'),
    path('<int:group_id>/delete/',    GroupDeleteView.as_view(),  name='group-delete'),
    path('<int:group_id>/members/',   GroupMembersView.as_view(), name='group-members'),

    # ── Join Requests ─────────────────────────────────────
    path('join-request/',             JoinRequestView.as_view(),    name='group-join-request'),
    path('my-requests/',              MyJoinRequestsView.as_view(), name='my-join-requests'),
    path('accept-request/',           AcceptRequestView.as_view(),  name='group-accept-request'),
    path('reject-request/',           RejectRequestView.as_view(),  name='group-reject-request'),

    # ── Lock / Unlock ─────────────────────────────────────
    path('lock/',                     LockGroupView.as_view(),   name='group-lock'),
    path('unlock/',                   UnlockGroupView.as_view(), name='group-unlock'),

    # ── Member Management ─────────────────────────────────
    path('remove-member/',            RemoveMemberView.as_view(), name='group-remove-member'),
    path('add-member/',               AddMemberView.as_view(),    name='group-add-member'),

    # ── Current User ──────────────────────────────────────
    path('my-groups/',                MyGroupsView.as_view(),     name='my-groups'),
]
