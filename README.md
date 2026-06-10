# NIC Project - User Management API

A Django REST Framework based User Management API with JWT authentication, role-based access control, user registration, profile update, password change, role/permission management, user transfer, and dashboard APIs.

## Features

- User registration
- JWT login and refresh token authentication
- Custom user model
- Role-based access control
- State admin, district admin, and common user support
- User profile update
- Password change
- Role and permission creation
- User transfer between districts
- Dashboard data based on user role
- SQLite support by default
- PostgreSQL support through environment variables

## Tech Stack

- Python
- Django
- Django REST Framework
- Simple JWT
- SQLite / PostgreSQL
- Pillow
- python-decouple

## Project Structure

```bash
NIC_project/
│
├── project/
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── permissions.py
│   │   └── admin.py
│   │
│   ├── manage.py
│   └── requirements.txt
│
├── template.py
├── .gitignore
└── README.md
