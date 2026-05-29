from django.contrib.auth.models import AbstractUser
from django.db import models


class State(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class District(models.Model):
    state = models.ForeignKey(State, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Permission(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    # No choices — allows STATE_ADMIN, DISTRICT_ADMIN, COMMON_USER
    # and any future custom roles to be created freely
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ManyToManyField(Permission, blank=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    mobile = models.CharField(max_length=15, unique=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, blank=True)
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)

    def __str__(self):
        return self.username

    def get_role_name(self):
        """Safe role name accessor — returns None if role not assigned."""
        return self.role.name if self.role else None


class UserTransfer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_district = models.ForeignKey(
        District,
        on_delete=models.SET_NULL,
        null=True, blank=True,         
    )
    to_district = models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name='transfers_in'
    )
    transferred_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transfers_made'
    )
    transferred_at = models.DateTimeField(auto_now_add=True)