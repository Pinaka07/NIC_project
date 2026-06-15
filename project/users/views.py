# project/users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.db import transaction
from django.views import View

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import User, Role, Permission, District, UserTransfer
from .forms import (
    UserLoginForm,
    UserRegistrationForm,
    EditProfileForm,
    UserTransferForm,
    PasswordChangeForm,
    RoleForm,
)
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    EditProfileSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserTransferSerializer,
    PasswordChangeSerializer,
)


# ─── TEMPLATE VIEWS (Session based) ──────────────────────────────────────────

class LoginView(View):
    """
    GET  /users/login/ → show login form
    POST /users/login/ → authenticate and login
    """
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        form = UserLoginForm()
        return render(request, 'users/login.html', {'form': form})

    def post(self, request):
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome, {user.username}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
        return render(request, 'users/login.html', {'form': form})


class LogoutView(View):
    """
    POST /users/logout/ → logout and redirect to login
    """
    def get(self, request):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class DashboardView(View):
    """
    GET /users/dashboard/
    Shows role-based dashboard.
    """
    def get(self, request):
        role_name = request.user.get_role_name()

        if role_name is None:
            messages.error(request, 'No role assigned. Contact your administrator.')
            return redirect('login')

        if role_name == 'STATE_ADMIN':
            context = {
                'role': 'STATE_ADMIN',
                'total_users':     User.objects.count(),
                'district_admins': User.objects.filter(role__name='DISTRICT_ADMIN').count(),
                'common_users':    User.objects.filter(role__name='COMMON_USER').count(),
                'total_districts': District.objects.count(),
            }
        elif role_name == 'DISTRICT_ADMIN':
            context = {
                'role':            'DISTRICT_ADMIN',
                'district':        request.user.district,
                'state':           request.user.state,
                'district_users':  User.objects.filter(district=request.user.district).count(),
                'common_users':    User.objects.filter(
                    district=request.user.district,
                    role__name='COMMON_USER'
                ).count(),
            }
        else:
            context = {
                'role':     role_name,
                'user':     request.user,
            }

        return render(request, 'users/dashboard.html', context)


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class RegisterUserView(View):
    """
    GET  /users/register/ → show registration form
    POST /users/register/ → save new user
    Only STATE_ADMIN can register new users.
    """
    def get(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can register new users.')
            return redirect('dashboard')
        form = UserRegistrationForm()
        return render(request, 'users/register.html', {'form': form})

    def post(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can register new users.')
            return redirect('dashboard')
        form = UserRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'User registered successfully.')
            return redirect('user_list')
        return render(request, 'users/register.html', {'form': form})


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class UserListView(View):
    """
    GET /users/list/
    STATE_ADMIN    → all users
    DISTRICT_ADMIN → users in own district
    COMMON_USER    → own profile only
    """
    def get(self, request):
        role_name = request.user.get_role_name()

        if role_name == 'STATE_ADMIN':
            users = User.objects.select_related('role', 'state', 'district').all()
        elif role_name == 'DISTRICT_ADMIN':
            users = User.objects.select_related('role', 'state', 'district').filter(
                district=request.user.district
            )
        else:
            users = User.objects.select_related('role', 'state', 'district').filter(
                id=request.user.id
            )

        return render(request, 'users/user_list.html', {'users': users})


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class EditUserProfileView(View):
    """
    GET  /users/edit/<pk>/ → show edit form
    POST /users/edit/<pk>/ → save changes
    """
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        self._check_access(request, pk)
        form = EditProfileForm(instance=user)
        return render(request, 'users/edit_profile.html', {'form': form, 'edit_user': user})

    def post(self, request, pk):
        user = get_object_or_404(User, id=pk)
        if not self._check_access(request, pk):
            messages.error(request, 'You do not have permission to edit this user.')
            return redirect('dashboard')
        form = EditProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('user_list')
        return render(request, 'users/edit_profile.html', {'form': form, 'edit_user': user})

    def _check_access(self, request, pk):
        role_name = request.user.get_role_name()
        if request.user.id == pk:
            return True
        if role_name == 'STATE_ADMIN':
            return True
        if role_name == 'DISTRICT_ADMIN':
            return User.objects.filter(id=pk, district=request.user.district).exists()
        return False


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class TransferUserView(View):
    """
    GET  /users/transfer/ → show transfer form
    POST /users/transfer/ → perform transfer
    Only STATE_ADMIN can transfer users.
    """
    def get(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can transfer users.')
            return redirect('dashboard')
        users = User.objects.select_related('district').all()
        form = UserTransferForm()
        return render(request, 'users/transfer.html', {'form': form, 'users': users})

    def post(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can transfer users.')
            return redirect('dashboard')

        form = UserTransferForm(request.POST)
        if form.is_valid():
            user_id    = form.cleaned_data['user_id']
            to_district = form.cleaned_data['district']

            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
                return redirect('transfer_user')

            if user.district == to_district:
                messages.error(request, 'User already belongs to this district.')
                return redirect('transfer_user')

            with transaction.atomic():
                UserTransfer.objects.create(
                    user=user,
                    from_district=user.district,
                    to_district=to_district,
                    transferred_by=request.user,
                )
                user.district = to_district
                user.state    = to_district.state
                user.save(update_fields=['district', 'state'])

            messages.success(request, f'{user.username} transferred to {to_district.name} successfully.')
            return redirect('user_list')

        users = User.objects.select_related('district').all()
        return render(request, 'users/transfer.html', {'form': form, 'users': users})


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class CreateRoleView(View):
    """
    GET  /users/create-role/ → show role form
    POST /users/create-role/ → save role with permissions
    Only STATE_ADMIN can create roles.
    """
    def get(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can create roles.')
            return redirect('dashboard')
        form = RoleForm()
        return render(request, 'users/create_role.html', {'form': form})

    def post(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can create roles.')
            return redirect('dashboard')
        form = RoleForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Role created successfully.')
            return redirect('dashboard')
        return render(request, 'users/create_role.html', {'form': form})


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class PasswordChangeView(View):
    """
    GET  /users/password-change/ → show form
    POST /users/password-change/ → change password
    """
    def get(self, request):
        form = PasswordChangeForm()
        return render(request, 'users/password_change.html', {'form': form})

    def post(self, request):
        form = PasswordChangeForm(request.POST)
        if form.is_valid():
            user = request.user
            if not user.check_password(form.cleaned_data['old_password']):
                messages.error(request, 'Current password is incorrect.')
                return render(request, 'users/password_change.html', {'form': form})
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            messages.success(request, 'Password changed successfully. Please login again.')
            return redirect('login')
        return render(request, 'users/password_change.html', {'form': form})


# ─── API VIEWS (kept for future frontend/mobile use) ─────────────────────────

class UserApiRootView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({
            'message': 'NIC User Management API',
            'endpoints': {
                'login':             '/api/users/login/',
                'register':          '/api/users/register/',
                'list_users':        '/api/users/list/',
                'dashboard':         '/api/users/dashboard/',
                'edit_profile':      '/api/users/edit/<id>/',
                'transfer_user':     '/api/users/transfer-user/',
                'create_role':       '/api/users/create-role/',
                'password_change':   '/api/users/password-change/',
            },
        })