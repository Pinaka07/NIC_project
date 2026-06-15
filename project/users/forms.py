# project/users/forms.py

from django import forms
from .models import User, Role, District, State


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter username'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password'
        })
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        })
    )

    class Meta:
        model = User
        fields = [
            'username', 'email', 'mobile',
            'role', 'state', 'district', 'profile_image'
        ]
        widgets = {
            'username':      forms.TextInput(attrs={'class': 'form-control'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile':        forms.TextInput(attrs={'class': 'form-control'}),
            'role':          forms.Select(attrs={'class': 'form-control'}),
            'state':         forms.Select(attrs={'class': 'form-control'}),
            'district':      forms.Select(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'mobile', 'profile_image']
        widgets = {
            'username':      forms.TextInput(attrs={'class': 'form-control'}),
            'email':         forms.EmailInput(attrs={'class': 'form-control'}),
            'mobile':        forms.TextInput(attrs={'class': 'form-control'}),
            'profile_image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if User.objects.exclude(pk=self.instance.pk).filter(mobile=mobile).exists():
            raise forms.ValidationError('This mobile number is already in use.')
        return mobile


class UserTransferForm(forms.Form):
    user_id = forms.IntegerField(widget=forms.HiddenInput())
    district = forms.ModelChoiceField(
        queryset=District.objects.all(),
        empty_label='Select District',
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Current password'
        })
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'New password'
        })
    )
    new_password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        new_password_confirm = cleaned_data.get('new_password_confirm')
        if new_password and new_password_confirm and new_password != new_password_confirm:
            raise forms.ValidationError('New passwords do not match.')
        return cleaned_data


class RoleForm(forms.ModelForm):
    class Meta:
        model = Role
        fields = ['name', 'permissions']
        widgets = {
            'name':        forms.TextInput(attrs={'class': 'form-control'}),
            'permissions': forms.CheckboxSelectMultiple(),
        }