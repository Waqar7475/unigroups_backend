"""
chat/urls.py — routes under /api/chat/
"""
from django.urls import path
from .views import GroupMessagesView, MessageDeleteView

urlpatterns = [
    path('groups/<int:group_id>/messages/', GroupMessagesView.as_view(), name='group-chat'),
    path('messages/<int:message_id>/',      MessageDeleteView.as_view(), name='message-delete'),
]
