from rest_framework.permissions import BasePermission


class IsStateAdmin(BasePermission):
    message = 'Only State Admin can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name == 'STATE_ADMIN'
        )


class IsDistrictAdmin(BasePermission):
    message = 'Only District Admin can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name == 'DISTRICT_ADMIN'
        )


class IsStateOrDistrictAdmin(BasePermission):
    message = 'Only State Admin or District Admin can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role is not None and
            request.user.role.name in ('STATE_ADMIN', 'DISTRICT_ADMIN')
        )