from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction

from .models import User, Role, Permission, District, UserTransfer
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    EditProfileSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserTransferSerializer,
    PasswordChangeSerializer,
)


class UserApiRootView(APIView):
    permission_classes = []

    def get(self, request):
        return Response({
            'message': 'NIC User Management API',
            'version': '1.0',
            'endpoints': {
                'login':              {'method': 'POST',  'url': '/api/users/login/'},
                'refresh':            {'method': 'POST',  'url': '/api/users/refresh/'},
                'register':           {'method': 'POST',  'url': '/api/users/register/'},
                'list_users':         {'method': 'GET',   'url': '/api/users/list/'},
                'edit_profile':       {'method': 'PATCH', 'url': '/api/users/edit/<id>/'},
                'password_change':    {'method': 'POST',  'url': '/api/users/password-change/'},
                'create_role':        {'method': 'POST',  'url': '/api/users/create-role/'},
                'create_permission':  {'method': 'POST',  'url': '/api/users/create-permission/'},
                'transfer_user':      {'method': 'POST',  'url': '/api/users/transfer-user/'},
                'dashboard':          {'method': 'GET',   'url': '/api/users/dashboard/'},
            },
        })


class RegisterUserView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {'message': 'User registered successfully.', 'user_id': user.id},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    permission_classes = []

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

        return Response(UserSerializer(users, many=True).data)


class EditUserProfileView(APIView):
    permission_classes = []

    def patch(self, request, pk):
        role_name = request.user.get_role_name()

        if request.user.id != pk:
            if role_name == 'STATE_ADMIN':
                pass
            elif role_name == 'DISTRICT_ADMIN':
                if not User.objects.filter(id=pk, district=request.user.district).exists():
                    return Response(
                        {'error': 'You can only edit users in your district.'},
                        status=status.HTTP_403_FORBIDDEN,
                    )
            else:
                return Response(
                    {'error': 'You cannot edit other users.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            user = User.objects.get(id=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = EditProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Profile updated successfully.', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreatePermissionView(APIView):
    """POST /api/users/create-permission/ — STATE_ADMIN only (enforced by middleware)."""
    permission_classes = []

    def post(self, request):
        serializer = PermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Permission created successfully.', 'data': serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateRoleView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Role created successfully.', 'data': serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransferUserView(APIView):
    permission_classes = []

    def post(self, request):
        user_id = request.data.get('user_id')
        to_district_id = request.data.get('to_district')

        if not user_id or not to_district_id:
            return Response(
                {'error': 'user_id and to_district are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            to_district = District.objects.get(id=to_district_id)
        except District.DoesNotExist:
            return Response({'error': 'District not found.'}, status=status.HTTP_404_NOT_FOUND)

        if user.district == to_district:
            return Response(
                {'error': 'User already belongs to this district.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            transfer = UserTransfer.objects.create(
                user=user,
                from_district=user.district,
                to_district=to_district,
                transferred_by=request.user,
            )
            user.district = to_district
            user.state = to_district.state
            user.save(update_fields=['district', 'state'])

        return Response({
            'message': 'User transferred successfully.',
            'data': UserTransferSerializer(transfer).data,
        })


class DashboardView(APIView):
    permission_classes = []

    def get(self, request):
        role_name = request.user.get_role_name()

        if role_name == 'STATE_ADMIN':
            data = {
                'role': 'STATE_ADMIN',
                'total_users': User.objects.count(),
                'district_admins': User.objects.filter(role__name='DISTRICT_ADMIN').count(),
                'common_users': User.objects.filter(role__name='COMMON_USER').count(),
                'total_districts': District.objects.count(),
                'total_states': District.objects.values('state').distinct().count(),
            }
        elif role_name == 'DISTRICT_ADMIN':
            data = {
                'role': 'DISTRICT_ADMIN',
                'district': request.user.district.name if request.user.district else 'N/A',
                'state': request.user.state.name if request.user.state else 'N/A',
                'district_users': User.objects.filter(district=request.user.district).count(),
                'common_users': User.objects.filter(
                    district=request.user.district,
                    role__name='COMMON_USER',
                ).count(),
            }
        else:
            data = {
                'role': role_name,
                'username': request.user.username,
                'email': request.user.email,
                'state': request.user.state.name if request.user.state else 'N/A',
                'district': request.user.district.name if request.user.district else 'N/A',
            }

        return Response(data)


class PasswordChangeView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': 'Password changed successfully.'})