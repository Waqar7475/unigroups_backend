"""
groups/views.py
"""
from django.utils   import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from users.models      import User
from users.permissions import IsAdminUser
from .models           import Group, GroupMember, JoinRequest
from .serializers      import (
    GroupListSerializer, GroupDetailSerializer,
    GroupCreateSerializer, GroupUpdateSerializer,
    JoinRequestSerializer, JoinRequestCreateSerializer,
    RequestActionSerializer, AddMemberSerializer,
    GroupMemberSerializer,
)


class GroupListView(APIView):
    """
    GET /api/groups/
    - Students automatically see their own department's groups + all others
    - ?dept=SE|CS  ?status=open|locked  ?search=text
    - Response includes by_department breakdown (SE and CS separately)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        groups = Group.objects.all().prefetch_related('memberships')

        dept_filter   = request.query_params.get('dept')
        status_filter = request.query_params.get('status')
        search        = request.query_params.get('search')

        if dept_filter:   groups = groups.filter(department=dept_filter)
        if status_filter: groups = groups.filter(status=status_filter)
        if search:        groups = groups.filter(name__icontains=search)

        all_list  = list(groups)
        se_groups = [g for g in all_list if g.department == 'SE']
        cs_groups = [g for g in all_list if g.department == 'CS']

        # If logged-in student has a department, mark their dept as "my_dept"
        my_dept = None
        if request.user.is_authenticated and not request.user.is_admin:
            my_dept = request.user.department

        return Response({
            'success':   True,
            'count':     len(all_list),
            'my_dept':   my_dept,
            'groups':    GroupListSerializer(all_list, many=True).data,
            'by_department': {
                'SE': {
                    'label':  'Software Engineering',
                    'is_mine': my_dept == 'SE',
                    'groups': GroupListSerializer(se_groups, many=True).data,
                },
                'CS': {
                    'label':  'Computer Science',
                    'is_mine': my_dept == 'CS',
                    'groups': GroupListSerializer(cs_groups, many=True).data,
                },
            }
        })


class GroupCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # If student: force department to their own
        data = request.data.copy()
        if not request.user.is_admin and request.user.department:
            data['department'] = request.user.department

        s = GroupCreateSerializer(data=data, context={'request': request})
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        group = s.save()
        return Response({
            'success': True,
            'message': f'Group "{group.name}" created. You are the leader.',
            'group':   GroupDetailSerializer(group, context={'request': request}).data,
        }, status=201)


class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:
            group = Group.objects.prefetch_related(
                'memberships__user', 'join_requests__user'
            ).get(pk=group_id)
        except Group.DoesNotExist:
            return Response({'success': False, 'message': 'Group not found.'}, status=404)
        return Response({
            'success': True,
            'group':   GroupDetailSerializer(group, context={'request': request}).data,
        })


class GroupUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, group_id):
        try:    group = Group.objects.get(pk=group_id)
        except: return Response({'success': False, 'message': 'Group not found.'}, status=404)

        is_leader = GroupMember.objects.filter(
            group=group, user=request.user, role=GroupMember.Role.LEADER
        ).exists()
        if not (is_leader or request.user.is_admin):
            return Response({'success': False, 'message': 'Only leader or admin.'}, status=403)

        s = GroupUpdateSerializer(group, data=request.data, partial=True)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        s.save()
        return Response({
            'success': True,
            'group':   GroupDetailSerializer(group, context={'request': request}).data,
        })


class GroupDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def delete(self, request, group_id):
        try:    group = Group.objects.get(pk=group_id)
        except: return Response({'success': False, 'message': 'Group not found.'}, status=404)
        name = group.name
        group.delete()
        return Response({'success': True, 'message': f'"{name}" deleted.'})


class JoinRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = JoinRequestCreateSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        group_id = s.validated_data['group_id']
        group    = Group.objects.get(pk=group_id)
        jr = JoinRequest.objects.create(
            group=group, user=request.user,
            message=s.validated_data.get('message', '')
        )
        return Response({
            'success': True,
            'message': f'Request sent to "{group.name}".',
            'request': JoinRequestSerializer(jr).data,
        }, status=201)


class MyJoinRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        reqs = JoinRequest.objects.filter(user=request.user).select_related('group', 'reviewed_by')
        return Response({'success': True, 'requests': JoinRequestSerializer(reqs, many=True).data})


class AcceptRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = RequestActionSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        jr = s.join_request
        if jr.group.is_full:
            return Response({'success': False, 'message': 'Group is full.'}, status=400)
        jr.status      = JoinRequest.RequestStatus.ACCEPTED
        jr.reviewed_by = request.user
        jr.reviewed_at = timezone.now()
        jr.save()
        GroupMember.objects.get_or_create(
            group=jr.group, user=jr.user,
            defaults={'role': GroupMember.Role.MEMBER}
        )
        if jr.group.is_full: jr.group.lock()
        return Response({'success': True, 'message': f'{jr.user.name} accepted into "{jr.group.name}".'})


class RejectRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        s = RequestActionSerializer(data=request.data, context={'request': request})
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        jr             = s.join_request
        jr.status      = JoinRequest.RequestStatus.REJECTED
        jr.reviewed_by = request.user
        jr.reviewed_at = timezone.now()
        jr.save()
        return Response({'success': True, 'message': f'Request from {jr.user.name} rejected.'})


class LockGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_id = request.data.get('group_id')
        if not group_id:
            return Response({'success': False, 'message': 'group_id required.'}, status=400)
        try:    group = Group.objects.get(pk=group_id)
        except: return Response({'success': False, 'message': 'Not found.'}, status=404)
        is_leader = GroupMember.objects.filter(
            group=group, user=request.user, role=GroupMember.Role.LEADER
        ).exists()
        if not (is_leader or request.user.is_admin):
            return Response({'success': False, 'message': 'Only leader or admin.'}, status=403)
        if group.is_locked:
            return Response({'success': False, 'message': 'Already locked.'})
        group.lock()
        return Response({'success': True, 'message': f'"{group.name}" locked.'})


class UnlockGroupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        group_id = request.data.get('group_id')
        if not group_id:
            return Response({'success': False, 'message': 'group_id required.'}, status=400)
        try:    group = Group.objects.get(pk=group_id)
        except: return Response({'success': False, 'message': 'Not found.'}, status=404)
        is_leader = GroupMember.objects.filter(
            group=group, user=request.user, role=GroupMember.Role.LEADER
        ).exists()
        if not (is_leader or request.user.is_admin):
            return Response({'success': False, 'message': 'Only leader or admin.'}, status=403)
        if not group.is_locked:
            return Response({'success': False, 'message': 'Not locked.'})
        group.unlock()
        return Response({'success': True, 'message': f'"{group.name}" unlocked.'})


class GroupMembersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, group_id):
        try:    group = Group.objects.get(pk=group_id)
        except: return Response({'success': False, 'message': 'Not found.'}, status=404)
        members = group.memberships.select_related('user').all()
        return Response({
            'success': True,
            'count':   members.count(),
            'members': GroupMemberSerializer(members, many=True).data,
        })


class RemoveMemberView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        group_id = request.data.get('group_id')
        user_id  = request.data.get('user_id')
        if not group_id or not user_id:
            return Response({'success': False, 'message': 'group_id and user_id required.'}, status=400)
        try:
            group  = Group.objects.get(pk=group_id)
            target = User.objects.get(pk=user_id)
        except (Group.DoesNotExist, User.DoesNotExist) as e:
            return Response({'success': False, 'message': str(e)}, status=404)
        is_leader = GroupMember.objects.filter(
            group=group, user=request.user, role=GroupMember.Role.LEADER
        ).exists()
        if not (is_leader or request.user.is_admin):
            return Response({'success': False, 'message': 'Only leader or admin.'}, status=403)
        membership = GroupMember.objects.filter(group=group, user=target).first()
        if not membership:
            return Response({'success': False, 'message': f'{target.name} is not a member.'}, status=404)
        membership.delete()
        if group.is_locked and not group.is_full:
            group.unlock()
        return Response({'success': True, 'message': f'{target.name} removed.'})


class AddMemberView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        s = AddMemberSerializer(data=request.data)
        if not s.is_valid():
            return Response({'success': False, 'errors': s.errors}, status=400)
        try:
            group = Group.objects.get(pk=s.validated_data['group_id'])
            user  = User.objects.get(pk=s.validated_data['user_id'])
        except (Group.DoesNotExist, User.DoesNotExist) as e:
            return Response({'success': False, 'message': str(e)}, status=404)
        if group.is_full:
            return Response({'success': False, 'message': 'Group is full.'}, status=400)
        if GroupMember.objects.filter(group=group, user=user).exists():
            return Response({'success': False, 'message': f'{user.name} already a member.'}, status=400)
        GroupMember.objects.create(group=group, user=user, role=s.validated_data['role'])
        if group.is_full: group.lock()
        return Response({'success': True, 'message': f'{user.name} added.'}, status=201)


class MyGroupsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = GroupMember.objects.filter(
            user=request.user
        ).select_related('group').prefetch_related('group__memberships')
        result = []
        for m in memberships:
            d           = GroupListSerializer(m.group).data
            d['my_role'] = m.role
            result.append(d)
        return Response({'success': True, 'count': len(result), 'groups': result})
