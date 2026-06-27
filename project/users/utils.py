def get_user_scope(user):
    from .models import User
    role = user.get_role_name()

    if role == 'STATE_ADMIN':
        return User.objects.select_related('role', 'state', 'district').all()
    elif role == 'DISTRICT_ADMIN':
        if user.district_id is None:
            return User.objects.none()
        return User.objects.select_related('role', 'state', 'district').filter(
            district_id=user.district_id
        )
    else:
        return User.objects.select_related('role', 'state', 'district').filter(
            id=user.id
        )


def check_role_access(user, required_role):
    role = user.get_role_name()
    hierarchy = ['COMMON_USER', 'DISTRICT_ADMIN', 'STATE_ADMIN']

    if role not in hierarchy or required_role not in hierarchy:
        return False

    return hierarchy.index(role) >= hierarchy.index(required_role)
