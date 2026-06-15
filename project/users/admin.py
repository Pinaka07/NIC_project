# project/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, Permission, State, District, UserTransfer


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'email', 'mobile', 'role', 'state', 'district', 'is_active']
    list_filter   = ['role', 'state', 'district', 'is_active']
    search_fields = ['username', 'email', 'mobile']
    ordering      = ['username']
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('mobile', 'role', 'state', 'district', 'profile_image')
        }),
    )


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display  = ['name']
    search_fields = ['name']
    filter_horizontal = ['permissions']


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display  = ['name']
    search_fields = ['name']


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display  = ['name']
    search_fields = ['name']


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display  = ['name', 'state']
    list_filter   = ['state']
    search_fields = ['name']


@admin.register(UserTransfer)
class UserTransferAdmin(admin.ModelAdmin):
    list_display  = ['user', 'from_district', 'to_district', 'transferred_by', 'transferred_at']
    list_filter   = ['to_district']
    search_fields = ['user__username']
    readonly_fields = ['transferred_at']