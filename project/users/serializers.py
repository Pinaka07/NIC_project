from rest_framework import serializers
from .models import User, Role, Permission, UserTransfer


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name']


class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(),
        many=True
    )
    permissions_detail = PermissionSerializer(
        source='permissions', many=True, read_only=True
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions', 'permissions_detail']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'mobile',
            'password', 'password_confirm',
            'role', 'state', 'district', 'profile_image',
        ]

    def validate(self, data):
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError('Passwords do not match.')
        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    role = serializers.StringRelatedField()
    state = serializers.StringRelatedField()
    district = serializers.StringRelatedField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'mobile',
            'role', 'state', 'district',
            'profile_image', 'date_joined',
        ]
        read_only_fields = fields


class EditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'email', 'mobile', 'profile_image']

    def validate_mobile(self, value):
        user = self.instance
        if User.objects.exclude(pk=user.pk).filter(mobile=value).exists():
            raise serializers.ValidationError('This mobile number is already in use.')
        return value


class UserTransferSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTransfer
        fields = '__all__'


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, data):
        if data['new_password'] != data.pop('new_password_confirm'):
            raise serializers.ValidationError('New passwords do not match.')
        return data