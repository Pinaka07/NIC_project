from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    LoginView,
    LogoutView,
    DashboardView,
    RegisterUserView,
    UserListView,
    EditUserProfileView,
    TransferUserView,
    TransferHistoryView,
    ToggleUserActiveView,
    CreateRoleView,
    PasswordChangeView,
    UserApiRootView,
)

urlpatterns = [
    # Template URLs (session based)
    path('login/',              LoginView.as_view(),             name='login'),
    path('logout/',              LogoutView.as_view(),            name='logout'),
    path('dashboard/',           DashboardView.as_view(),         name='dashboard'),
    path('register/',            RegisterUserView.as_view(),      name='register'),
    path('list/',                UserListView.as_view(),          name='user_list'),
    path('edit/<int:pk>/',       EditUserProfileView.as_view(),   name='edit_profile'),
    path('transfer/',            TransferUserView.as_view(),      name='transfer_user'),
    path('transfer-history/',    TransferHistoryView.as_view(),   name='transfer_history'),
    path('toggle-active/<int:pk>/', ToggleUserActiveView.as_view(), name='toggle_active'),
    path('create-role/',         CreateRoleView.as_view(),        name='create_role'),
    path('password-change/',     PasswordChangeView.as_view(),    name='password_change'),

    # API URLs (JWT based — for future use)
    path('api/',         UserApiRootView.as_view(),     name='api_root'),
    path('api/login/',   TokenObtainPairView.as_view(), name='api_login'),
    path('api/refresh/', TokenRefreshView.as_view(),    name='api_refresh'),
]