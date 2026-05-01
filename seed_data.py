"""
seed_data.py - Fresh seed with roll_number login + email verification
"""
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unigroups_project.settings')
django.setup()

from users.models  import User
from groups.models import Group, GroupMember, JoinRequest

# Clear
JoinRequest.objects.all().delete()
GroupMember.objects.all().delete()
Group.objects.all().delete()
User.objects.all().delete()

print("🌱 Seeding...")

# Admin
admin = User.objects.create_superuser(
    roll_number='SU00-ADMIN-A00-001',
    name='Admin User',
    email='admin@superior.edu.pk',
    password='admin123',
)

# SE Students
se_students = [
    ('SU72-BSSEM-F25-001', 'Ali Hassan',   'ali@superior.edu.pk'),
    ('SU72-BSSEM-F25-002', 'Sara Khan',    'sara@superior.edu.pk'),
    ('SU72-BSSEM-F25-003', 'Usman Tariq',  'usman@superior.edu.pk'),
    ('SU72-BSSEM-F25-004', 'Hamza Saeed',  'hamza@superior.edu.pk'),
    ('SU72-BSSEM-F25-005', 'Nida Fatima',  'nida@superior.edu.pk'),
]
cs_students = [
    ('SU72-BSCS-F25-001', 'Bilal Ahmed',  'bilal@superior.edu.pk'),
    ('SU72-BSCS-F25-002', 'Zara Sheikh',  'zara@superior.edu.pk'),
    ('SU72-BSCS-F25-003', 'Omar Farooq',  'omar@superior.edu.pk'),
    ('SU72-BSCS-F25-004', 'Amna Raza',    'amna@superior.edu.pk'),
]

se_users, cs_users = [], []
for rn, name, email in se_students:
    u = User.objects.create_user(roll_number=rn, name=name, email=email,
                                  password='pass1234', department='SE', is_verified=True)
    se_users.append(u)

for rn, name, email in cs_students:
    u = User.objects.create_user(roll_number=rn, name=name, email=email,
                                  password='pass1234', department='CS', is_verified=True)
    cs_users.append(u)

print(f"  ✓ {User.objects.count()} users")

# SE Groups
g1 = Group.objects.create(name='Alpha Dev Squad', department='SE',
    description='Full-stack web app for final year.', max_members=5, created_by=se_users[0])
GroupMember.objects.create(group=g1, user=se_users[0], role='leader')
GroupMember.objects.create(group=g1, user=se_users[1], role='member')
GroupMember.objects.create(group=g1, user=se_users[2], role='member')
JoinRequest.objects.create(group=g1, user=se_users[3], message='I want to join!')

g2 = Group.objects.create(name='SE Research Group', department='SE',
    description='AI research project.', max_members=4, created_by=se_users[3])
GroupMember.objects.create(group=g2, user=se_users[3], role='leader')
GroupMember.objects.create(group=g2, user=se_users[4], role='member')

# CS Groups
g3 = Group.objects.create(name='CS Innovators', department='CS',
    description='Cloud computing project.', max_members=4, created_by=cs_users[0])
GroupMember.objects.create(group=g3, user=cs_users[0], role='leader')
GroupMember.objects.create(group=g3, user=cs_users[1], role='member')

g4 = Group.objects.create(name='Data Science Lab', department='CS',
    description='ML experiments.', max_members=5, created_by=cs_users[2])
GroupMember.objects.create(group=g4, user=cs_users[2], role='leader')
GroupMember.objects.create(group=g4, user=cs_users[3], role='member')

print(f"  ✓ {Group.objects.count()} groups")
print(f"  ✓ {GroupMember.objects.count()} memberships")
print(f"  ✓ {JoinRequest.objects.count()} join requests")
print("\n✅ Seed complete!")
print("\nLogin with Roll Number:")
print("  Admin: SU00-ADMIN-A00-001  / admin123")
print("  SE:    SU72-BSSEM-F25-001  / pass1234")
print("  CS:    SU72-BSCS-F25-001   / pass1234")
