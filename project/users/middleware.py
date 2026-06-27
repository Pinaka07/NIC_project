# project/users/middleware.py

from django.shortcuts import redirect

# URLs that anyone can access without login
PUBLIC_URLS = [
    '/users/login/',
    '/admin/',
    '/static/',
    '/media/',
]


class RoleMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # DRF performs JWT authentication and permission checks inside the view.
        if path.startswith('/users/api/'):
            return self.get_response(request)

        # Allow public URLs without any check
        if any(path.startswith(url) for url in PUBLIC_URLS):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect('/users/login/')

        return self.get_response(request)
