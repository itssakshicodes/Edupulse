"""
core/views.py
Central dashboard router — redirects each role to its own dashboard.
Also handles email notifications via Django signals.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q

from results.models import Result, Subject, Batch, UploadLog
from accounts.models import Profile


@login_required
def dashboard(request):
    """
    Single entry point — renders role-specific dashboard widget data
    and dispatches to the correct template.
    """
    user    = request.user
    profile = getattr(user, 'profile', None)
    role    = profile.role if profile else 'student'

    if user.is_superuser or role == 'admin':
        return _admin_dashboard(request)
    elif role == 'faculty':
        return _faculty_dashboard(request)
    elif role == 'hod':
        return _hod_dashboard(request)
    else:
        return _student_dashboard(request)


# ── Role-specific dashboard helpers ──────────────────────────────────────

def _admin_dashboard(request):
    total_users    = User.objects.count()
    total_results  = Result.objects.count()
    total_subjects = Subject.objects.count()
    total_batches  = Batch.objects.count()
    recent_logs    = UploadLog.objects.select_related('uploaded_by').all()[:5]

    # Pass / Fail counts
    pass_count = Result.objects.filter(is_pass=True).count()
    fail_count = total_results - pass_count

    # Role distribution for the user pill cards
    role_counts = {r[0]: Profile.objects.filter(role=r[0]).count() for r in Profile.ROLE_CHOICES}

    return render(request, 'core/dashboard_admin.html', {
        'total_users':    total_users,
        'total_results':  total_results,
        'total_subjects': total_subjects,
        'total_batches':  total_batches,
        'pass_count':     pass_count,
        'fail_count':     fail_count,
        'recent_logs':    recent_logs,
        'role_counts':    role_counts,
    })


def _faculty_dashboard(request):
    # Subjects with performance summary
    subjects = Subject.objects.annotate(
        avg_marks=Avg('results__marks_obtained'),
        total_results=Count('results'),
        pass_count=Count('results', filter=Q(results__is_pass=True)),
    )
    recent_results = Result.objects.filter(
        uploaded_by=request.user
    ).select_related('student', 'subject').order_by('-upload_date')[:10]

    return render(request, 'core/dashboard_faculty.html', {
        'subjects':       subjects,
        'recent_results': recent_results,
        'total_uploaded': Result.objects.filter(uploaded_by=request.user).count(),
    })


def _hod_dashboard(request):
    total_results = Result.objects.count()
    pass_count    = Result.objects.filter(is_pass=True).count()
    avg_marks     = Result.objects.aggregate(avg=Avg('marks_obtained'))['avg'] or 0

    # Department-wise breakdown
    dept_stats = (Result.objects.values('subject__department')
                                .annotate(
                                    avg=Avg('marks_obtained'),
                                    total=Count('id'),
                                    passes=Count('id', filter=Q(is_pass=True)),
                                )
                                .order_by('subject__department'))

    return render(request, 'core/dashboard_hod.html', {
        'total_results': total_results,
        'pass_count':    pass_count,
        'fail_count':    total_results - pass_count,
        'pass_rate':     round((pass_count / total_results * 100) if total_results else 0, 1),
        'avg_marks':     round(avg_marks, 2),
        'dept_stats':    dept_stats,
    })


def _student_dashboard(request):
    results  = Result.objects.filter(student=request.user).select_related('subject', 'batch')
    total    = results.count()
    passes   = results.filter(is_pass=True).count()
    avg      = results.aggregate(avg=Avg('marks_obtained'))['avg'] or 0

    # Semester-wise summary
    sem_summary = (results.values('semester')
                          .annotate(avg=Avg('marks_obtained'), total=Count('id'),
                                    passes=Count('id', filter=Q(is_pass=True)))
                          .order_by('semester'))

    return render(request, 'core/dashboard_student.html', {
        'results':     results,
        'total':       total,
        'passes':      passes,
        'fails':       total - passes,
        'avg_marks':   round(avg, 2),
        'sem_summary': sem_summary,
        'cgpa':        round(avg / 10, 2),
    })
