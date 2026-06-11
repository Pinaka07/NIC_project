from django.http import JsonResponse


ROLE_PROTECTED_URLS = {
    'STATE_ADMIN': [
        '/api/users/create-role/',
        '/api/users/create-permission/',
        '/api/users/transfer-user/',
        '/api/users/list/',
    ],
    'DISTRICT_ADMIN': [
        '/api/users/list/',
    ],
}

PUBLIC_URLS = [
    '/api/users/login/',
    '/api/users/refresh/',
    '/api/users/register/',
    '/api/users/',
    '/admin/',
]


class RoleMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Allow public URLs without any check
        if any(path.startswith(url) for url in PUBLIC_URLS):
            return self.get_response(request)

        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return JsonResponse(
                {'error': 'Authentication required. Please login.'},
                status=401
            )

        # Get user role safely
        role_name = request.user.role.name if request.user.role else None

        if role_name is None:
            return JsonResponse(
                {'error': 'No role assigned. Contact your administrator.'},
                status=403
            )

        # Check STATE_ADMIN only URLs
        state_admin_urls = ROLE_PROTECTED_URLS['STATE_ADMIN']
        if any(path.startswith(url) for url in state_admin_urls):
            if role_name not in ('STATE_ADMIN',):
                # District admin can access list only
                if path.startswith('/api/users/list/') and role_name == 'DISTRICT_ADMIN':
                    return self.get_response(request)
                return JsonResponse(
                    {'error': 'Only State Admin can perform this action.'},
                    status=403
                )

        return self.get_response(request)