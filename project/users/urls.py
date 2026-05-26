from django.urls import path

from .views import (
    RegisterUserView,
    UserListView,
    EditUserProfileView,
    CreatePermissionView,
    CreateRoleView,
    TransferUserView,
    DashboardView,
    PasswordChangeView
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView
)

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('register/', RegisterUserView.as_view(), name='register'),

    path('list/', UserListView.as_view(), name='user_list'),
    path('edit/<int:pk>/', EditUserProfileView.as_view(), name='edit_profile'),
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),

    path('create-role/', CreateRoleView.as_view(), name='create_role'),
    path('create-permission/', CreatePermissionView.as_view(), name='create_permission'),

    path('transfer-user/', TransferUserView.as_view(), name='transfer_user'),

    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
