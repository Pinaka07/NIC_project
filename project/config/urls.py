# project/config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/',  admin.site.urls),
    path('users/',  include('users.urls')),
    path('',        lambda request: redirect('login')),  # root → login page
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)