"""
accounts/views.py
Authentication views + user management (admin only).
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError

from .forms import LoginForm, UserRegistrationForm, ProfileForm, UserUpdateForm
from .models import Profile
from .decorators import admin_required


# ── Authentication ───────────────────────────────────────────────────────

def login_view(request):
    """Handles login and role-based redirection."""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect(request.GET.get('next', 'core:dashboard'))
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('accounts:login')


# ── User Management (Admin) ──────────────────────────────────────────────

@admin_required
def user_list(request):
    """Admin: list all users with role filter."""
    role_filter = request.GET.get('role', '')
    users = User.objects.select_related('profile').all().order_by('-date_joined')
    if role_filter:
        users = users.filter(profile__role=role_filter)
    return render(request, 'accounts/user_list.html', {
        'users': users,
        'role_filter': role_filter,
        'roles': Profile.ROLE_CHOICES,
    })


@admin_required
def user_create(request):
    """Admin creates a new user + assigns role."""
    user_form    = UserRegistrationForm()
    profile_form = ProfileForm()

    if request.method == 'POST':
        user_form    = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            try:
                user = user_form.save()
                # Profile was auto-created via signal; now update it
                profile = user.profile
                profile.role        = profile_form.cleaned_data['role']
                profile.department  = profile_form.cleaned_data['department']
                profile.phone       = profile_form.cleaned_data['phone']
                profile.roll_number = profile_form.cleaned_data['roll_number']
                profile.bio         = profile_form.cleaned_data['bio']
                profile.save()
                messages.success(request, f"User '{user.username}' created successfully.")
                return redirect('accounts:user_list')
            except IntegrityError:
                messages.error(request, "Roll number already exists.")
        else:
            messages.error(request, "Please fix the errors below.")

    return render(request, 'accounts/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'action': 'Create',
    })


@admin_required
def user_edit(request, pk):
    """Admin edits an existing user."""
    target_user  = get_object_or_404(User, pk=pk)
    user_form    = UserUpdateForm(instance=target_user)
    profile_form = ProfileForm(instance=target_user.profile)

    if request.method == 'POST':
        user_form    = UserUpdateForm(request.POST, instance=target_user)
        profile_form = ProfileForm(request.POST, instance=target_user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "User updated successfully.")
            return redirect('accounts:user_list')

    return render(request, 'accounts/user_form.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'action': 'Edit',
        'target_user': target_user,
    })


@admin_required
def user_delete(request, pk):
    target_user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f"User '{username}' deleted.")
        return redirect('accounts:user_list')
    return render(request, 'accounts/user_confirm_delete.html', {'target_user': target_user})


@login_required
def profile_view(request):
    """Any user can view/edit their own profile."""
    user_form    = UserUpdateForm(instance=request.user)
    profile_form = ProfileForm(instance=request.user.profile)

    if request.method == 'POST':
        user_form    = UserUpdateForm(request.POST, instance=request.user)
        # Students cannot change their own role
        profile_form = ProfileForm(request.POST, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            p = profile_form.save(commit=False)
            if not request.user.is_superuser:
                p.role = request.user.profile.role   # lock role for non-admins
            p.save()
            messages.success(request, "Profile updated.")
            return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })
