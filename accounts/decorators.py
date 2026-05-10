"""
accounts/decorators.py
Role-Based Access Control (RBAC) decorators.
Usage:
    @login_required
    @role_required('admin', 'hod')
    def my_view(request): ...
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def role_required(*roles):
    """
    Decorator factory — restricts a view to users whose profile.role
    is in the supplied list of role strings.
    Always chains after @login_required.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            # Superusers bypass all role checks
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            try:
                user_role = request.user.profile.role
            except AttributeError:
                messages.error(request, "Your account has no profile. Contact admin.")
                return redirect('accounts:login')

            if user_role in roles:
                return view_func(request, *args, **kwargs)

            messages.error(request, f"Access denied. This page requires one of: {', '.join(roles)}.")
            return redirect('core:dashboard')
        return wrapper
    return decorator


# ── Shorthand decorators ─────────────────────────────────────────────────
def admin_required(view_func):
    return role_required('admin')(view_func)

def faculty_required(view_func):
    return role_required('admin', 'faculty')(view_func)

def hod_required(view_func):
    return role_required('admin', 'hod')(view_func)

def student_required(view_func):
    return role_required('student')(view_func)

def staff_required(view_func):
    """Admin + Faculty + HOD — anyone except plain students."""
    return role_required('admin', 'faculty', 'hod')(view_func)
