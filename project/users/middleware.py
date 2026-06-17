# project/users/middleware.py

from django.http import JsonResponse
from django.shortcuts import redirect

# URLs that anyone can access without login
PUBLIC_URLS = [
    '/users/login/',
    '/users/logout/',
    '/admin/',
    '/api/users/login/',
    '/api/users/refresh/',
    '/api/users/register/',
    '/api/users/api/',
    '/static/',
    '/media/',
]

# API URLs that need STATE_ADMIN role
STATE_ADMIN_URLS = [
    '/api/users/create-role/',
    '/api/users/create-permission/',
    '/api/users/transfer-user/',
]


class RoleMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Allow public URLs without any check
        if any(path.startswith(url) for url in PUBLIC_URLS):
            return self.get_response(request)

        # For template URLs redirect to login if not authenticated
        if not path.startswith('/api/'):
            if not request.user.is_authenticated:
                return redirect('/users/login/')
            return self.get_response(request)

        # For API URLs return JSON error if not authenticated
        if not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required. Please login.'},
                status=401
            )

        # Get user role safely
        role_name = request.user.role.name if request.user.role else None

        # Check STATE_ADMIN only API URLs
        if any(path.startswith(url) for url in STATE_ADMIN_URLS):
            if role_name != 'STATE_ADMIN':
                return JsonResponse(
                    {'error': 'Only State Admin can perform this action.'},
                    status=403
                )

        return self.get_response(request)