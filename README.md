# UniGroups Backend — Django REST API

University Group Management System built with **Django 4.2** and **Django REST Framework**.

---

## 📁 Project Structure

```
unigroups_backend/
├── manage.py
├── requirements.txt
├── seed_data.py                  ← Sample data for dev/testing
├── db.sqlite3                    ← SQLite database (auto-created)
│
├── unigroups_project/            ← Django project config
│   ├── settings.py               ← All settings (JWT, CORS, DRF)
│   ├── urls.py                   ← Root URL routing
│   ├── wsgi.py
│   └── asgi.py
│
├── users/                        ← Authentication & user management
│   ├── models.py                 ← Custom User model (email login, roles)
│   ├── serializers.py            ← Register, Login, Profile serializers
│   ├── views.py                  ← Auth views (register, login, profile)
│   ├── permissions.py            ← IsAdminUser, IsOwnerOrAdmin
│   ├── urls.py                   ← /api/auth/* routes
│   └── admin.py
│
├── groups/                       ← Group management
│   ├── models.py                 ← Group, GroupMember, JoinRequest
│   ├── serializers.py            ← All group serializers
│   ├── views.py                  ← All group API views
│   ├── permissions.py            ← IsGroupLeader, IsGroupMember
│   ├── urls.py                   ← /api/groups/* routes
│   └── admin.py
│
└── chat/                         ← Basic group chat (REST polling)
    ├── models.py                 ← Message model
    ├── serializers.py
    ├── views.py                  ← Send / receive messages
    ├── urls.py                   ← /api/chat/* routes
    └── admin.py
```

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Apply database migrations
python manage.py migrate

# 3. (Optional) Seed sample data
python seed_data.py

# 4. Create superuser (if not using seed data)
python manage.py createsuperuser

# 5. Start the development server
python manage.py runserver
```

---

## 🔑 Authentication

All protected routes require a JWT **Bearer token** in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Tokens expire after **24 hours**. Use the refresh endpoint to get a new access token.

---

## 📡 API Reference

### Auth  (`/api/auth/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register/` | ❌ | Register + auto-login (returns tokens) |
| POST | `/login/` | ❌ | Login with email + password |
| POST | `/logout/` | ✅ | Blacklist refresh token |
| POST | `/token/refresh/` | ❌ | Get new access token |
| GET  | `/profile/` | ✅ | View own profile |
| PATCH | `/profile/` | ✅ | Update own name |
| POST | `/change-password/` | ✅ | Change password |
| GET  | `/users/` | 🔒 Admin | List all users |
| PATCH | `/users/<id>/role/` | 🔒 Admin | Promote / demote user |

### Groups  (`/api/groups/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/` | ❌ | List all groups (filterable) |
| POST | `/create/` | ✅ | Create group (you become leader) |
| GET | `/<id>/` | ✅ | Full group detail + members |
| PATCH | `/<id>/update/` | Leader/Admin | Update group info |
| DELETE | `/<id>/delete/` | 🔒 Admin | Delete group |
| GET | `/<id>/members/` | ✅ | List members |
| POST | `/join-request/` | ✅ | Send join request |
| GET | `/my-requests/` | ✅ | My join request history |
| POST | `/accept-request/` | Leader/Admin | Accept a join request |
| POST | `/reject-request/` | Leader/Admin | Reject a join request |
| POST | `/lock/` | Leader/Admin | Lock group (no more requests) |
| POST | `/unlock/` | Leader/Admin | Unlock group |
| DELETE | `/remove-member/` | Leader/Admin | Remove a member |
| POST | `/add-member/` | 🔒 Admin | Add member directly |
| GET | `/my-groups/` | ✅ | Groups I belong to |

### Chat  (`/api/chat/`)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/groups/<id>/messages/` | Member | Fetch message history |
| POST | `/groups/<id>/messages/` | Member | Send a message |
| DELETE | `/messages/<id>/` | Owner/Admin | Delete a message |

---

## 📋 Request / Response Examples

### Register
```http
POST /api/auth/register/
Content-Type: application/json

{
  "name": "Ali Hassan",
  "email": "ali@superior.edu.pk",
  "password": "SecurePass123!",
  "password2": "SecurePass123!"
}
```
```json
{
  "success": true,
  "message": "Account created successfully.",
  "user": { "id": 1, "name": "Ali Hassan", "email": "ali@superior.edu.pk", "role": "student" },
  "access_token": "eyJ...",
  "refresh_token": "eyJ..."
}
```

### Create Group
```http
POST /api/groups/create/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Alpha Dev Squad",
  "subject": "Software Engineering",
  "max_members": 5,
  "description": "Final year project group."
}
```

### Send Join Request
```http
POST /api/groups/join-request/
Authorization: Bearer <token>
Content-Type: application/json

{
  "group_id": 1,
  "message": "I'd love to join your team!"
}
```

### Accept Request
```http
POST /api/groups/accept-request/
Authorization: Bearer <leader_token>
Content-Type: application/json

{ "request_id": 3 }
```

---

## 👤 User Roles

| Role | Capabilities |
|------|-------------|
| `student` | Register, create groups, send join requests, chat in joined groups |
| `admin` | Everything + edit/delete any group, add/remove any member, manage user roles |

### Group Roles

| Role | Capabilities |
|------|-------------|
| `leader` | Edit group, accept/reject requests, lock/unlock, remove members |
| `member` | View group, access chat |

---

## 🛠 Tech Stack

- **Django 4.2** — web framework
- **Django REST Framework** — REST API toolkit
- **Simple JWT** — JWT authentication with token blacklisting
- **django-cors-headers** — CORS for frontend integration
- **SQLite** — development database (swap for PostgreSQL in production)

---

## 🔒 Production Checklist

- [ ] Set `DEBUG = False` in settings
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `ALLOWED_HOSTS` to your domain
- [ ] Switch to PostgreSQL (`psycopg2`)
- [ ] Set `CORS_ALLOWED_ORIGINS` (remove `CORS_ALLOW_ALL_ORIGINS`)
- [ ] Use environment variables for secrets (e.g. `python-decouple`)
- [ ] Run `python manage.py collectstatic`
- [ ] Deploy with Gunicorn + Nginx
