"""
chat/serializers.py
====================
Serializers for chat messages.
"""
from rest_framework import serializers
from users.serializers import UserProfileSerializer
from .models import Message


class MessageSerializer(serializers.ModelSerializer):
    """Full message with nested sender info."""
    sender = UserProfileSerializer(read_only=True)

    class Meta:
        model  = Message
        fields = ['id', 'group', 'sender', 'content', 'is_edited', 'created_at', 'updated_at']
        read_only_fields = ['id', 'sender', 'is_edited', 'created_at', 'updated_at']


class MessageCreateSerializer(serializers.ModelSerializer):
    """Used when sending a new message."""
    class Meta:
        model  = Message
        fields = ['content']

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError('Message cannot be empty.')
        return value.strip()
