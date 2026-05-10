"""
core/signals.py
Django signals for email notifications:
  - After result saved → check for low performance alert
  - After bulk upload → notify uploader
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender='results.Result')
def check_low_performance(sender, instance, created, **kwargs):
    """
    Send an email alert when a student scores below 40 (fail).
    Fires only on newly created results to avoid spam on edits.
    """
    if not created:
        return
    if not instance.is_pass:
        student = instance.student
        subject_name = instance.subject.name
        marks = instance.marks_obtained

        # Email to student
        if student.email:
            send_mail(
                subject=f"[EduPulse] Low Performance Alert — {subject_name}",
                message=(
                    f"Dear {student.get_full_name() or student.username},\n\n"
                    f"You have scored {marks} marks in {subject_name} (Semester {instance.semester}), "
                    f"which is below the passing threshold.\n\n"
                    f"Please contact your faculty for guidance.\n\n"
                    f"— EduPulse Academic System"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student.email],
                fail_silently=True,
            )
