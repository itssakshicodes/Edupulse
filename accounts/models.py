"""
accounts/models.py
Extends Django's default User with role-based profiles.
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    """
    One-to-one extension of the default Django User.
    Stores role, department, and contact info.
    """
    ROLE_CHOICES = [
        ('admin',   'Admin'),
        ('faculty', 'Faculty'),
        ('hod',     'HOD / Management'),
        ('student', 'Student'),
    ]

    user        = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role        = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    department  = models.CharField(max_length=100, blank=True, null=True)
    phone       = models.CharField(max_length=15, blank=True, null=True)
    # For students: their enrollment / roll number
    roll_number = models.CharField(max_length=30, blank=True, null=True, unique=True)
    avatar      = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio         = models.TextField(blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    # ── Convenience role checks ──────────────────────────────────────────
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_faculty(self):
        return self.role == 'faculty'

    @property
    def is_hod(self):
        return self.role == 'hod'

    @property
    def is_student(self):
        return self.role == 'student'


# ── Signal: auto-create Profile when a new User is saved ────────────────
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
