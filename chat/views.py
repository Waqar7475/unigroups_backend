"""
chat/views.py
==============
Basic REST polling endpoints for group chat.
Future: upgrade to Django Channels + WebSockets.

Routes (under /api/chat/):
  GET  /groups/<group_id>/messages/  — fetch message history
  POST /groups/<group_id>/messages/  — send a message
  DELETE /messages/<message_id>/     — delete own message
"""
from rest_framework             import status
from rest_framework.views       import APIView
from rest_framework.response    import Response
from rest_framework.permissions import IsAuthenticated

from groups.models  import Group, GroupMember
from .models        import Message
from .serializers   import MessageSerializer, MessageCreateSerializer


class GroupMessagesView(APIView):
    """
    GET  /api/chat/groups/<group_id>/messages/  — list messages (members only)
    POST /api/chat/groups/<group_id>/messages/  — send a message (members only)
    """
    permission_classes = [IsAuthenticated]

    def _get_group_or_error(self, group_id, user):
        """Returns (group, error_response). Only members can access chat."""
        try:
            group = Group.objects.get(pk=group_id)
        except Group.DoesNotExist:
            return None, Response(
                {'success': False, 'message': 'Group not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        is_member = GroupMember.objects.filter(group=group, user=user).exists()
        if not (is_member or user.is_admin):
            return None, Response(
                {'success': False, 'message': 'Only group members can access the chat.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        return group, None

    def get(self, request, group_id):
        group, err = self._get_group_or_error(group_id, request.user)
        if err:
            return err

        # Optional: last N messages
        limit    = int(request.query_params.get('limit', 50))
        messages = Message.objects.filter(group=group).select_related('sender').order_by('-created_at')[:limit]
        messages = list(reversed(messages))   # chronological order

        return Response({
            'success':  True,
            'group':    group.name,
            'count':    len(messages),
            'messages': MessageSerializer(messages, many=True).data,
        })

    def post(self, request, group_id):
        group, err = self._get_group_or_error(group_id, request.user)
        if err:
            return err

        serializer = MessageCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'success': False, 'errors': serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        msg = Message.objects.create(
            group=group,
            sender=request.user,
            content=serializer.validated_data['content'],
        )
        return Response({
            'success': True,
            'message': MessageSerializer(msg).data,
        }, status=status.HTTP_201_CREATED)


class MessageDeleteView(APIView):
    """
    DELETE /api/chat/messages/<message_id>/
    Users can delete their own messages. Admins can delete any.
    """
    permission_classes = [IsAuthenticated]

    def delete(self, request, message_id):
        try:
            msg = Message.objects.get(pk=message_id)
        except Message.DoesNotExist:
            return Response(
                {'success': False, 'message': 'Message not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if msg.sender != request.user and not request.user.is_admin:
            return Response(
                {'success': False, 'message': 'You can only delete your own messages.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        msg.delete()
        return Response({'success': True, 'message': 'Message deleted.'})
