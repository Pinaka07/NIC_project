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

from .models import User, Role, Permission, District, UserTransfer
from .utils import get_user_scope
from .forms import (
    UserLoginForm,
    UserRegistrationForm,
    EditProfileForm,
    UserTransferForm,
    PasswordChangeForm,
    RoleForm,
)


class LoginView(View):
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
    def post(self, request):
        logout(request)
        messages.success(request, 'You have been logged out.')
        return redirect('login')


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class DashboardView(View):
    def get(self, request):
        role_name = request.user.get_role_name()

        if role_name is None:
            logout(request)
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
            district_users = (
                User.objects.filter(district_id=request.user.district_id)
                if request.user.district_id is not None
                else User.objects.none()
            )
            context = {
                'role':            'DISTRICT_ADMIN',
                'district':        request.user.district,
                'state':           request.user.state,
                'district_users':  district_users.count(),
                'common_users':    district_users.filter(role__name='COMMON_USER').count(),
            }
        else:
            context = {
                'role':     role_name,
                'user':     request.user,
            }

        return render(request, 'users/dashboard.html', context)


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class RegisterUserView(View):
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
    STATE_ADMIN    -> all users
    DISTRICT_ADMIN -> users in own district
    COMMON_USER    -> own profile only
    Supports ?search=username filtering.
    """
    def get(self, request):
        users = get_user_scope(request.user)
        search = request.GET.get('search', '')
        if search:
            users = users.filter(username__icontains=search)
        return render(request, 'users/user_list.html', {'users': users, 'search': search})


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class EditUserProfileView(View):
    def get(self, request, pk):
        user = get_object_or_404(User, id=pk)
        if not self._check_access(request, pk):
            messages.error(request, 'You do not have permission to edit this user.')
            return redirect('dashboard')
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
            return (
                request.user.district_id is not None
                and User.objects.filter(
                    id=pk,
                    district_id=request.user.district_id,
                ).exists()
            )
        return False


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class TransferUserView(View):
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
            user_id     = form.cleaned_data['user_id']
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
class TransferHistoryView(View):
    """STATE_ADMIN can view all user transfer records."""
    def get(self, request):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can view transfer history.')
            return redirect('dashboard')
        transfers = UserTransfer.objects.select_related(
            'user', 'from_district', 'to_district', 'transferred_by'
        ).order_by('-transferred_at')
        return render(request, 'users/transfer_history.html', {'transfers': transfers})


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class ToggleUserActiveView(View):
    """STATE_ADMIN can activate/deactivate a user instead of deleting."""
    def post(self, request, pk):
        if request.user.get_role_name() != 'STATE_ADMIN':
            messages.error(request, 'Only State Admin can perform this action.')
            return redirect('user_list')
        user = get_object_or_404(User, id=pk)
        if user == request.user:
            messages.error(request, 'You cannot deactivate your own account.')
            return redirect('user_list')
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
        messages.success(request, f'{user.username} is now {"active" if user.is_active else "inactive"}.')
        return redirect('user_list')


@method_decorator(login_required(login_url='/users/login/'), name='dispatch')
class CreateRoleView(View):
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


class UserApiRootView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({
            'message': 'NIC User Management API',
            'endpoints': {
                'token_login':   '/users/api/login/',
                'token_refresh': '/users/api/refresh/',
            },
        })
