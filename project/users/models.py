from django.contrib.auth.models import AbstractUser
from django.db import models

class State(models.Model):
    name=models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name

class District(models.Model):
    state=models.ForeignKey(State,on_delete=models.CASCADE)
    name=models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Permission(models.Model):
    name=models.CharField(max_length=100,unique=True)

    def __str__(self):
        return self.name

class Role(models.Model):

    ROLE_CHOICES=[
        ('STATE_ADMIN','State Admin'),
        ('DISTRICT_ADMIN','District Admin'),
        ('COMMON_USER','Common User')
    ]

    name=models.CharField(max_length=30,choices=ROLE_CHOICES,unique=True)
    permissions=models.ManyToManyField(Permission,blank=True)

    def __str__(self):
        return self.name

class User(AbstractUser):

    mobile=models.CharField(max_length=15,unique=True)
    role=models.ForeignKey(Role,on_delete=models.SET_NULL,null=True)
    state=models.ForeignKey(State,on_delete=models.SET_NULL,null=True,blank=True)
    district=models.ForeignKey(District,on_delete=models.SET_NULL,null=True,blank=True)
    profile_image=models.ImageField(upload_to='profiles/',null=True,blank=True)

    def __str__(self):
        return self.username

class UserTransfer(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    from_district=models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name='from_district'
    )
    to_district=models.ForeignKey(
        District,
        on_delete=models.CASCADE,
        related_name='to_district'
    )
    transferred_by=models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='transferred_by'
    )
    transferred_at=models.DateTimeField(auto_now_add=True)
