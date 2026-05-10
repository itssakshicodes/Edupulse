"""
analytics/views.py
Analytics dashboards with Google Charts data.
All chart data is returned as JSON via AJAX endpoints.
"""
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Q, FloatField
from django.db.models.functions import Round

from accounts.decorators import staff_required, hod_required
from results.models import Result, Subject, Batch


# ── HOD / Management Dashboard ───────────────────────────────────────────

@hod_required
def institution_dashboard(request):
    """Overview analytics for HOD/Management."""
    total_students = Result.objects.values('student').distinct().count()
    total_results  = Result.objects.count()
    pass_count     = Result.objects.filter(is_pass=True).count()
    fail_count     = total_results - pass_count
    avg_marks      = Result.objects.aggregate(avg=Avg('marks_obtained'))['avg'] or 0

    context = {
        'total_students': total_students,
        'total_results':  total_results,
        'pass_count':     pass_count,
        'fail_count':     fail_count,
        'pass_rate':      round((pass_count / total_results * 100) if total_results else 0, 1),
        'avg_marks':      round(avg_marks, 2),
        'batches':        Batch.objects.all(),
        'subjects':       Subject.objects.all(),
    }
    return render(request, 'analytics/institution.html', context)


# ── Faculty Subject Dashboard ─────────────────────────────────────────────

@staff_required
def subject_dashboard(request):
    """Subject-level performance analysis."""
    subjects = Subject.objects.annotate(
        avg_marks=Round(Avg('results__marks_obtained'), 2),
        total=Count('results'),
        passes=Count('results', filter=Q(results__is_pass=True)),
    )
    context = {'subjects': subjects}
    return render(request, 'analytics/subject_dashboard.html', context)


# ── Student Personal Dashboard ────────────────────────────────────────────

@login_required
def student_dashboard(request):
    """Student views their own performance."""
    results = Result.objects.filter(student=request.user).select_related('subject', 'batch')

    semesters = sorted(results.values_list('semester', flat=True).distinct())
    avg_by_sem = []
    for sem in semesters:
        avg = results.filter(semester=sem).aggregate(avg=Avg('marks_obtained'))['avg'] or 0
        avg_by_sem.append({'semester': sem, 'avg': round(avg, 2)})

    context = {
        'results':      results,
        'avg_by_sem':   avg_by_sem,
        'total':        results.count(),
        'passes':       results.filter(is_pass=True).count(),
        'cgpa':         _calc_cgpa(results),
        'semesters':    semesters,
    }
    return render(request, 'analytics/student_dashboard.html', context)


def _calc_cgpa(results):
    """Rough CGPA on 10-point scale."""
    if not results.exists():
        return 0.0
    total_marks = sum(r.marks_obtained for r in results)
    return round((total_marks / results.count()) / 10, 2)


# ═══════════════════════════════════════════════════════════════════
# JSON API endpoints for Google Charts (AJAX)
# ═══════════════════════════════════════════════════════════════════

@staff_required
def chart_pass_fail(request):
    """Pie chart — overall pass vs fail."""
    semester = request.GET.get('semester')
    batch_id = request.GET.get('batch')
    qs = Result.objects.all()
    if semester:
        qs = qs.filter(semester=semester)
    if batch_id:
        qs = qs.filter(batch_id=batch_id)
    passes = qs.filter(is_pass=True).count()
    fails  = qs.filter(is_pass=False).count()
    data = [['Status', 'Count'], ['Pass', passes], ['Fail', fails]]
    return JsonResponse({'data': data})


@staff_required
def chart_grade_distribution(request):
    """Column chart — grade counts."""
    semester = request.GET.get('semester')
    subject_id = request.GET.get('subject')
    qs = Result.objects.all()
    if semester:
        qs = qs.filter(semester=semester)
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    grade_order = ['O', 'A+', 'A', 'B+', 'B', 'C', 'F']
    counts = dict(qs.values('grade').annotate(cnt=Count('grade')).values_list('grade', 'cnt'))
    data = [['Grade', 'Students']] + [[g, counts.get(g, 0)] for g in grade_order]
    return JsonResponse({'data': data})


@staff_required
def chart_semester_trend(request):
    """Line chart — average marks per semester."""
    batch_id = request.GET.get('batch')
    subject_id = request.GET.get('subject')
    qs = Result.objects.all()
    if batch_id:
        qs = qs.filter(batch_id=batch_id)
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    trend = (qs.values('semester')
               .annotate(avg=Round(Avg('marks_obtained'), 2))
               .order_by('semester'))
    data = [['Semester', 'Average Marks']] + [[f"Sem {t['semester']}", float(t['avg'])] for t in trend]
    return JsonResponse({'data': data})


@staff_required
def chart_subject_comparison(request):
    """Bar chart — average marks per subject."""
    semester = request.GET.get('semester')
    batch_id = request.GET.get('batch')
    qs = Result.objects.all()
    if semester:
        qs = qs.filter(semester=semester)
    if batch_id:
        qs = qs.filter(batch_id=batch_id)
    subj_data = (qs.values('subject__name')
                   .annotate(avg=Round(Avg('marks_obtained'), 2))
                   .order_by('-avg')[:15])
    data = [['Subject', 'Average Marks']] + [[s['subject__name'], float(s['avg'])] for s in subj_data]
    return JsonResponse({'data': data})


@staff_required
def chart_scatter(request):
    """Scatter plot — individual student performance."""
    semester = request.GET.get('semester')
    subject_id = request.GET.get('subject')
    qs = Result.objects.all()
    if semester:
        qs = qs.filter(semester=semester)
    if subject_id:
        qs = qs.filter(subject_id=subject_id)
    points = list(qs.values('student__id', 'marks_obtained')
                    .annotate(avg=Round(Avg('marks_obtained'), 2))
                    .order_by('student__id')[:100])
    data = [['Student Index', 'Marks']] + [[i+1, float(p['marks_obtained'])] for i, p in enumerate(points)]
    return JsonResponse({'data': data})


@login_required
def chart_student_trend(request):
    """Line chart for a specific student (own trend)."""
    if request.user.profile.is_student:
        student_id = request.user.id
    else:
        student_id = request.GET.get('student_id', request.user.id)

    trend = (Result.objects.filter(student_id=student_id)
                           .values('semester')
                           .annotate(avg=Round(Avg('marks_obtained'), 2))
                           .order_by('semester'))
    data = [['Semester', 'Average Marks']] + [[f"Sem {t['semester']}", float(t['avg'])] for t in trend]
    return JsonResponse({'data': data})
