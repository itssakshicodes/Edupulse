"""
accounts/forms.py
Authentication and profile management forms.
"""
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import Profile


class LoginForm(AuthenticationForm):
    """Styled login form."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Username or Email',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Password',
        })
    )


class UserRegistrationForm(UserCreationForm):
    """Admin creates users via this form."""
    email       = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name  = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name   = forms.CharField(required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model  = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class ProfileForm(forms.ModelForm):
    """Edit role + profile details."""
    class Meta:
        model   = Profile
        fields  = ['role', 'department', 'phone', 'roll_number', 'bio']
        widgets = {
            'role':        forms.Select(attrs={'class': 'form-select'}),
            'department':  forms.TextInput(attrs={'class': 'form-control'}),
            'phone':       forms.TextInput(attrs={'class': 'form-control'}),
            'roll_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio':         forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class UserUpdateForm(forms.ModelForm):
    """Update basic User fields."""
    class Meta:
        model  = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'email':      forms.EmailInput(attrs={'class': 'form-control'}),
        }
