from django.contrib import admin
from .models import (
    User,
    Role,
    Permission,
    State,
    District,
    UserTransfer
)

admin.site.register(User)
admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(State)
admin.site.register(District)
admin.site.register(UserTransfer)