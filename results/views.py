"""
results/views.py
Result upload, listing, manual entry, CSV export, PDF report.
"""
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.db.models import Q, Avg, Count

from accounts.decorators import faculty_required, admin_required, staff_required
from .models import Result, Subject, Batch, UploadLog
from .forms import ResultUploadForm, ResultFilterForm, ManualResultForm, SubjectForm, BatchForm
from .utils import parse_csv, validate_and_import, generate_csv_report


# ── Upload ───────────────────────────────────────────────────────────────

@faculty_required
def upload_results(request):
    """
    Two-stage upload:
    1. Parse file → show preview + errors
    2. User confirms → save
    """
    form = ResultUploadForm()
    preview_errors = None
    success_count  = 0

    if request.method == 'POST':
        form = ResultUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            try:
                rows = parse_csv(uploaded_file)
                if not rows:
                    messages.error(request, "The uploaded file is empty.")
                else:
                    success_count, error_count, errors = validate_and_import(
                        rows, request.user, uploaded_file.name
                    )
                    if error_count == 0:
                        messages.success(request, f"✅ {success_count} result(s) imported successfully.")
                    else:
                        messages.warning(
                            request,
                            f"⚠️ {success_count} imported, {error_count} failed. See error report below."
                        )
                        preview_errors = errors
            except ValueError as e:
                messages.error(request, f"File error: {e}")
            except Exception as e:
                messages.error(request, f"Unexpected error: {e}")

    return render(request, 'results/upload.html', {
        'form': form,
        'preview_errors': preview_errors,
        'success_count': success_count,
    })


# ── Result List ──────────────────────────────────────────────────────────

@staff_required
def result_list(request):
    """Paginated, filterable result table for admin/faculty/hod."""
    form    = ResultFilterForm(request.GET or None)
    results = Result.objects.select_related('student', 'subject', 'batch', 'student__profile').all()

    if form.is_valid():
        if form.cleaned_data.get('semester'):
            results = results.filter(semester=form.cleaned_data['semester'])
        if form.cleaned_data.get('subject'):
            results = results.filter(subject=form.cleaned_data['subject'])
        if form.cleaned_data.get('batch'):
            results = results.filter(batch=form.cleaned_data['batch'])
        if form.cleaned_data.get('grade'):
            results = results.filter(grade=form.cleaned_data['grade'])
        if form.cleaned_data.get('date_from'):
            results = results.filter(upload_date__date__gte=form.cleaned_data['date_from'])
        if form.cleaned_data.get('date_to'):
            results = results.filter(upload_date__date__lte=form.cleaned_data['date_to'])

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(results, 25)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'results/result_list.html', {
        'form': form,
        'page_obj': page_obj,
        'total': results.count(),
    })


# ── Manual Entry ─────────────────────────────────────────────────────────

@faculty_required
def result_create(request):
    form = ManualResultForm()
    if request.method == 'POST':
        form = ManualResultForm(request.POST)
        if form.is_valid():
            result = form.save(commit=False)
            result.uploaded_by = request.user
            result.save()
            messages.success(request, "Result saved successfully.")
            return redirect('results:result_list')
    return render(request, 'results/result_form.html', {'form': form, 'action': 'Add'})


@faculty_required
def result_edit(request, pk):
    result = get_object_or_404(Result, pk=pk)
    form   = ManualResultForm(request.POST or None, instance=result)
    if form.is_valid():
        form.save()
        messages.success(request, "Result updated.")
        return redirect('results:result_list')
    return render(request, 'results/result_form.html', {'form': form, 'action': 'Edit', 'result': result})


@admin_required
def result_delete(request, pk):
    result = get_object_or_404(Result, pk=pk)
    if request.method == 'POST':
        result.delete()
        messages.success(request, "Result deleted.")
        return redirect('results:result_list')
    return render(request, 'results/result_confirm_delete.html', {'result': result})


# ── Export ───────────────────────────────────────────────────────────────

@staff_required
def export_csv(request):
    """Download filtered results as CSV."""
    results = Result.objects.all()
    if request.GET.get('semester'):
        results = results.filter(semester=request.GET['semester'])
    if request.GET.get('subject'):
        results = results.filter(subject_id=request.GET['subject'])
    if request.GET.get('batch'):
        results = results.filter(batch_id=request.GET['batch'])

    csv_data = generate_csv_report(results)
    response  = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="results_export.csv"'
    return response


@login_required
def export_pdf(request):
    """Generate PDF report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        import io as _io

        if request.user.profile.is_student:
            results = Result.objects.filter(student=request.user).select_related('subject', 'batch')
            title   = f"Academic Report — {request.user.get_full_name()}"
        else:
            results = Result.objects.all().select_related('student', 'subject', 'batch', 'student__profile')
            title   = "EduPulse — Full Academic Report"

        buffer = _io.BytesIO()
        doc    = SimpleDocTemplate(buffer, pagesize=landscape(A4))
        styles = getSampleStyleSheet()
        elements = [Paragraph(title, styles['Title']), Spacer(1, 12)]

        data = [['Roll No', 'Name', 'Subject', 'Sem', 'Marks', 'Grade', 'Status', 'Batch']]
        for r in results:
            rn = getattr(getattr(r.student, 'profile', None), 'roll_number', '-') or '-'
            data.append([
                rn,
                r.student.get_full_name(),
                r.subject.name,
                str(r.semester),
                str(r.marks_obtained),
                r.grade,
                'Pass' if r.is_pass else 'Fail',
                r.batch.name,
            ])

        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a1a2e')),
            ('TEXTCOLOR',  (0,0), (-1,0), colors.white),
            ('FONTNAME',   (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE',   (0,0), (-1,0), 10),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f4ff')]),
            ('GRID',       (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE',   (0,1), (-1,-1), 8),
            ('ALIGN',      (0,0), (-1,-1), 'CENTER'),
        ]))
        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="edupulse_report.pdf"'
        return response

    except ImportError:
        messages.error(request, "ReportLab is not installed. Run: pip install reportlab")
        return redirect('core:dashboard')


# ── Upload Logs ──────────────────────────────────────────────────────────

@admin_required
def upload_logs(request):
    logs = UploadLog.objects.select_related('uploaded_by').all()[:50]
    return render(request, 'results/upload_logs.html', {'logs': logs})


# ── Subject & Batch Management ───────────────────────────────────────────

@admin_required
def subject_list(request):
    subjects = Subject.objects.all()
    return render(request, 'results/subject_list.html', {'subjects': subjects})

@admin_required
def subject_create(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Subject created.")
        return redirect('results:subject_list')
    return render(request, 'results/subject_form.html', {'form': form, 'action': 'Add'})

@admin_required
def subject_edit(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    form    = SubjectForm(request.POST or None, instance=subject)
    if form.is_valid():
        form.save()
        messages.success(request, "Subject updated.")
        return redirect('results:subject_list')
    return render(request, 'results/subject_form.html', {'form': form, 'action': 'Edit'})

@admin_required
def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'results/batch_list.html', {'batches': batches})

@admin_required
def batch_create(request):
    form = BatchForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Batch created.")
        return redirect('results:batch_list')
    return render(request, 'results/batch_form.html', {'form': form, 'action': 'Add'})


# ── AJAX: Filter subjects by semester ────────────────────────────────────

def ajax_subjects(request):
    semester = request.GET.get('semester')
    subjects = Subject.objects.filter(semester=semester).values('id', 'name', 'code') if semester else []
    return JsonResponse({'subjects': list(subjects)})
