"""
groups/serializers.py
"""
from rest_framework import serializers
from users.serializers import UserProfileSerializer
from .models import Group, GroupMember, JoinRequest


class GroupMemberSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)

    class Meta:
        model  = GroupMember
        fields = ['id', 'user', 'role', 'joined_at']
        read_only_fields = fields


class JoinRequestSerializer(serializers.ModelSerializer):
    user        = UserProfileSerializer(read_only=True)
    reviewed_by = UserProfileSerializer(read_only=True)
    group_name  = serializers.SerializerMethodField()

    class Meta:
        model  = JoinRequest
        fields = ['id', 'group', 'group_name', 'user', 'status', 'message',
                  'reviewed_by', 'reviewed_at', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'reviewed_at', 'created_at']

    def get_group_name(self, obj):
        return obj.group.name


class GroupListSerializer(serializers.ModelSerializer):
    member_count        = serializers.ReadOnlyField()
    slots_remaining     = serializers.ReadOnlyField()
    leader_name         = serializers.SerializerMethodField()
    department_display  = serializers.SerializerMethodField()

    class Meta:
        model  = Group
        fields = [
            'id', 'name', 'department', 'department_display',
            'description', 'max_members', 'member_count',
            'slots_remaining', 'status', 'is_locked',
            'leader_name', 'created_at',
        ]

    def get_leader_name(self, obj):
        leader = obj.get_leader()
        return leader.name if leader else None

    def get_department_display(self, obj):
        return obj.get_department_display()


class GroupDetailSerializer(serializers.ModelSerializer):
    members             = GroupMemberSerializer(source='memberships', many=True, read_only=True)
    member_count        = serializers.ReadOnlyField()
    slots_remaining     = serializers.ReadOnlyField()
    created_by          = UserProfileSerializer(read_only=True)
    pending_requests    = serializers.SerializerMethodField()
    department_display  = serializers.SerializerMethodField()

    class Meta:
        model  = Group
        fields = [
            'id', 'name', 'department', 'department_display',
            'description', 'max_members', 'member_count', 'slots_remaining',
            'status', 'is_locked', 'created_by',
            'members', 'pending_requests',
            'created_at', 'updated_at',
        ]

    def get_department_display(self, obj):
        return obj.get_department_display()

    def get_pending_requests(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return []
        user      = request.user
        is_leader = obj.memberships.filter(user=user, role=GroupMember.Role.LEADER).exists()
        if not (is_leader or user.is_admin):
            return []
        pending = obj.join_requests.filter(status=JoinRequest.RequestStatus.PENDING)
        return JoinRequestSerializer(pending, many=True).data


class GroupCreateSerializer(serializers.ModelSerializer):
    """
    Group creation — department is SE or CS only.
    member_ids: list of user IDs the creator wants to add as members.
    """
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        write_only=True,
    )

    class Meta:
        model  = Group
        fields = ['id', 'name', 'department', 'description', 'max_members', 'member_ids']
        extra_kwargs = {
            'description': {'required': False},
            'department':  {'required': True},
        }

    def validate_department(self, value):
        valid = [d[0] for d in Group.Department.choices]
        if value not in valid:
            raise serializers.ValidationError(f'Must be one of: {valid}')
        return value

    def validate_max_members(self, value):
        if value < 2:  raise serializers.ValidationError('Minimum 2 members.')
        if value > 20: raise serializers.ValidationError('Maximum 20 members.')
        return value

    def create(self, validated_data):
        member_ids = validated_data.pop('member_ids', [])
        user       = self.context['request'].user
        group      = Group.objects.create(created_by=user, **validated_data)

        # Creator is leader
        GroupMember.objects.create(group=group, user=user, role=GroupMember.Role.LEADER)

        # Add selected members from the list
        from users.models import User as UserModel
        for uid in member_ids:
            if uid == user.id:
                continue  # skip leader
            try:
                member_user = UserModel.objects.get(pk=uid)
                GroupMember.objects.get_or_create(
                    group=group, user=member_user,
                    defaults={'role': GroupMember.Role.MEMBER}
                )
            except UserModel.DoesNotExist:
                pass

        return group


class GroupUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Group
        fields = ['name', 'department', 'description', 'max_members']
        extra_kwargs = {'max_members': {'required': False}, 'department': {'required': False}}

    def validate_max_members(self, value):
        group = self.instance
        if group and value < group.member_count:
            raise serializers.ValidationError(
                f'Cannot set below current member count ({group.member_count}).'
            )
        return value


class JoinRequestCreateSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    message  = serializers.CharField(required=False, allow_blank=True, default='')

    def validate_group_id(self, value):
        try:
            group = Group.objects.get(pk=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError('Group not found.')
        user = self.context['request'].user
        if group.is_locked:  raise serializers.ValidationError('Group is locked.')
        if group.is_full:    raise serializers.ValidationError('Group is full.')
        if GroupMember.objects.filter(group=group, user=user).exists():
            raise serializers.ValidationError('You are already a member.')
        if JoinRequest.objects.filter(group=group, user=user, status=JoinRequest.RequestStatus.PENDING).exists():
            raise serializers.ValidationError('You already have a pending request.')
        return value


class RequestActionSerializer(serializers.Serializer):
    request_id = serializers.IntegerField()

    def validate_request_id(self, value):
        try:
            jr = JoinRequest.objects.select_related('group', 'user').get(pk=value)
        except JoinRequest.DoesNotExist:
            raise serializers.ValidationError('Join request not found.')
        if jr.status != JoinRequest.RequestStatus.PENDING:
            raise serializers.ValidationError(f'Request already {jr.status}.')
        requester = self.context['request'].user
        is_leader = GroupMember.objects.filter(
            group=jr.group, user=requester, role=GroupMember.Role.LEADER
        ).exists()
        if not (is_leader or requester.is_admin):
            raise serializers.ValidationError('Only the leader or admin can act on this.')
        self.join_request = jr
        return value


class AddMemberSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    user_id  = serializers.IntegerField()
    role     = serializers.ChoiceField(choices=GroupMember.Role.choices, default=GroupMember.Role.MEMBER)
