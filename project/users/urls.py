from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    UserApiRootView,
    RegisterUserView,
    UserListView,
    EditUserProfileView,
    CreatePermissionView,
    CreateRoleView,
    TransferUserView,
    DashboardView,
    PasswordChangeView,
)

urlpatterns = [
    path('', UserApiRootView.as_view(), name='user_api_root'),

    # Auth
    path('login/',   TokenObtainPairView.as_view(), name='token_obtain'),
    path('refresh/', TokenRefreshView.as_view(),    name='token_refresh'),

    # User management
    path('register/',         RegisterUserView.as_view(),    name='register'),
    path('list/',             UserListView.as_view(),         name='user_list'),
    path('edit/<int:pk>/',    EditUserProfileView.as_view(),  name='edit_profile'),
    path('password-change/',  PasswordChangeView.as_view(),   name='password_change'),

    # Role & permission management (STATE_ADMIN only)
    path('create-role/',       CreateRoleView.as_view(),       name='create_role'),
    path('create-permission/', CreatePermissionView.as_view(), name='create_permission'),

    # Transfer (STATE_ADMIN only)
    path('transfer-user/', TransferUserView.as_view(), name='transfer_user'),

    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
