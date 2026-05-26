from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from .models import User, Role, Permission, District, UserTransfer

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    RoleSerializer,
    PermissionSerializer,
    UserTransferSerializer,
    PasswordChangeSerializer
)

class RegisterUserView(APIView):

    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'User registered successfully',
                'user_id': serializer.data['id']
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            if request.user.role.name == 'STATE_ADMIN':
                users = User.objects.all()
            elif request.user.role.name == 'DISTRICT_ADMIN':
                users = User.objects.filter(district=request.user.district)
            else:
                users = User.objects.filter(id=request.user.id)

            serializer = UserSerializer(users, many=True)
            return Response(serializer.data)
        except Exception as e:
            return Response({
                'error': 'Failed to fetch users',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EditUserProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            if request.user.id != pk and request.user.role.name not in ['STATE_ADMIN', 'DISTRICT_ADMIN']:
                return Response({
                    'error': 'You cannot edit other users'
                }, status=status.HTTP_403_FORBIDDEN)

            user = User.objects.get(id=pk)
            serializer = UserSerializer(user, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({
                    'message': 'Profile updated successfully',
                    'data': serializer.data
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to update profile',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CreatePermissionView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role.name != 'STATE_ADMIN':
            return Response({
                'error': 'Only State Admin can create permissions'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = PermissionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Permission created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateRoleView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role.name != 'STATE_ADMIN':
            return Response({
                'error': 'Only State Admin can create roles'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Role created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TransferUserView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role.name != 'STATE_ADMIN':
            return Response({
                'error': 'Only State Admin can transfer users'
            }, status=status.HTTP_403_FORBIDDEN)

        try:
            user_id = request.data.get('user_id')
            to_district_id = request.data.get('to_district')

            if not user_id or not to_district_id:
                return Response({
                    'error': 'user_id and to_district are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.get(id=user_id)
            to_district = District.objects.get(id=to_district_id)

            if user.district == to_district:
                return Response({
                    'error': 'User already belongs to this district'
                }, status=status.HTTP_400_BAD_REQUEST)

            with transaction.atomic():
                serializer = UserTransferSerializer(data={
                    'user': user.id,
                    'from_district': user.district.id if user.district else None,
                    'to_district': to_district.id,
                    'transferred_by': request.user.id
                })

                if serializer.is_valid():
                    serializer.save()
                    user.district = to_district
                    user.save()

                    return Response({
                        'message': 'User transferred successfully',
                        'data': serializer.data
                    })
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except District.DoesNotExist:
            return Response({
                'error': 'District not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                'error': 'Failed to transfer user',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            role = request.user.role.name

            if role == 'STATE_ADMIN':
                data = {
                    'total_users': User.objects.count(),
                    'district_admins': User.objects.filter(
                        role__name='DISTRICT_ADMIN'
                    ).count(),
                    'common_users': User.objects.filter(
                        role__name='COMMON_USER'
                    ).count(),
                    'total_districts': District.objects.count(),
                    'total_states': District.objects.values('state').distinct().count()
                }
            elif role == 'DISTRICT_ADMIN':
                data = {
                    'district_name': request.user.district.name if request.user.district else 'N/A',
                    'district_users': User.objects.filter(
                        district=request.user.district
                    ).count(),
                    'common_users': User.objects.filter(
                        district=request.user.district,
                        role__name='COMMON_USER'
                    ).count()
                }
            else:
                data = {
                    'username': request.user.username,
                    'email': request.user.email,
                    'role': request.user.role.name,
                    'state': request.user.state.name if request.user.state else 'N/A',
                    'district': request.user.district.name if request.user.district else 'N/A'
                }

            return Response(data)
        except Exception as e:
            return Response({
                'error': 'Failed to load dashboard',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PasswordChangeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = PasswordChangeSerializer(data=request.data)
            if serializer.is_valid():
                user = request.user
                if not user.check_password(serializer.validated_data['old_password']):
                    return Response({
                        'error': 'Current password is incorrect'
                    }, status=status.HTTP_400_BAD_REQUEST)

                user.set_password(serializer.validated_data['new_password'])
                user.save()

                return Response({
                    'message': 'Password changed successfully'
                })
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'error': 'Failed to change password',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
