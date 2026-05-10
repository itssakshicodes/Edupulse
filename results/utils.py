"""
results/utils.py
CSV / Excel parsing, validation, grade logic, and report generation.
"""
import csv
import io
import json
from typing import List, Tuple, Dict

from django.contrib.auth.models import User
from django.db import transaction

from .models import Result, Subject, Batch, UploadLog


# ── Expected CSV columns ─────────────────────────────────────────────────
REQUIRED_COLUMNS = {'roll_number', 'subject_code', 'semester', 'batch_name', 'marks_obtained'}


def parse_csv(file_obj) -> List[Dict]:
    """Read CSV or Excel and return list of row dicts."""
    filename = getattr(file_obj, 'name', '')

    if filename.endswith(('.xlsx', '.xls')):
        return _parse_excel(file_obj)

    # CSV
    decoded = file_obj.read().decode('utf-8-sig')   # handle BOM
    reader  = csv.DictReader(io.StringIO(decoded))
    return [row for row in reader]


def _parse_excel(file_obj) -> List[Dict]:
    """Parse xlsx using openpyxl."""
    try:
        import openpyxl
        wb   = openpyxl.load_workbook(file_obj, read_only=True, data_only=True)
        ws   = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return []
        headers = [str(h).strip().lower().replace(' ', '_') for h in rows[0]]
        return [dict(zip(headers, row)) for row in rows[1:] if any(row)]
    except ImportError:
        raise ImportError("openpyxl is required for Excel uploads. Install it: pip install openpyxl")


def validate_and_import(rows: List[Dict], uploaded_by, file_name: str) -> Tuple[int, int, List[Dict]]:
    """
    Validate each row, save valid ones, collect errors.
    Returns (success_count, error_count, error_list).
    """
    errors       = []
    success_rows = 0
    error_rows   = 0

    # Normalise column names
    normalised = []
    for i, row in enumerate(rows, start=2):   # start=2 because row 1 = header
        normalised.append({k.strip().lower().replace(' ', '_'): str(v).strip() if v is not None else ''
                           for k, v in row.items()})

    # Check required columns exist
    if normalised:
        missing = REQUIRED_COLUMNS - set(normalised[0].keys())
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(missing)}")

    with transaction.atomic():
        for line_no, row in enumerate(normalised, start=2):
            row_errors = []

            # ── Required field presence ──────────────────────────────────
            for col in REQUIRED_COLUMNS:
                if not row.get(col):
                    row_errors.append(f"'{col}' is empty")

            if row_errors:
                errors.append({'row': line_no, 'data': row, 'errors': row_errors})
                error_rows += 1
                continue

            # ── Marks range ──────────────────────────────────────────────
            try:
                marks = float(row['marks_obtained'])
                if not (0 <= marks <= 100):
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({'row': line_no, 'data': row, 'errors': ['marks_obtained must be 0–100']})
                error_rows += 1
                continue

            # ── Semester range ───────────────────────────────────────────
            try:
                semester = int(row['semester'])
                if not (1 <= semester <= 10):
                    raise ValueError()
            except (ValueError, TypeError):
                errors.append({'row': line_no, 'data': row, 'errors': ['semester must be 1–10']})
                error_rows += 1
                continue

            # ── Resolve FK objects ───────────────────────────────────────
            # Student lookup via roll_number on Profile
            try:
                from accounts.models import Profile
                profile = Profile.objects.get(roll_number=row['roll_number'])
                student = profile.user
            except Exception:
                errors.append({'row': line_no, 'data': row,
                               'errors': [f"No student found with roll_number '{row['roll_number']}'"]})
                error_rows += 1
                continue

            try:
                subject = Subject.objects.get(code=row['subject_code'])
            except Subject.DoesNotExist:
                errors.append({'row': line_no, 'data': row,
                               'errors': [f"Subject code '{row['subject_code']}' not found"]})
                error_rows += 1
                continue

            try:
                batch = Batch.objects.get(name=row['batch_name'])
            except Batch.DoesNotExist:
                errors.append({'row': line_no, 'data': row,
                               'errors': [f"Batch '{row['batch_name']}' not found"]})
                error_rows += 1
                continue

            # ── Duplicate check ──────────────────────────────────────────
            if Result.objects.filter(student=student, subject=subject, semester=semester, batch=batch).exists():
                errors.append({'row': line_no, 'data': row,
                               'errors': ['Duplicate entry — result already uploaded']})
                error_rows += 1
                continue

            # ── Save ─────────────────────────────────────────────────────
            try:
                Result.objects.create(
                    student=student,
                    subject=subject,
                    batch=batch,
                    semester=semester,
                    marks_obtained=marks,
                    uploaded_by=uploaded_by,
                    remarks=row.get('remarks', ''),
                )
                success_rows += 1
            except Exception as e:
                errors.append({'row': line_no, 'data': row, 'errors': [str(e)]})
                error_rows += 1

    # ── Write audit log ──────────────────────────────────────────────────
    status = 'success' if error_rows == 0 else ('failed' if success_rows == 0 else 'partial')
    UploadLog.objects.create(
        uploaded_by=uploaded_by,
        file_name=file_name,
        total_rows=len(normalised),
        success_rows=success_rows,
        error_rows=error_rows,
        status=status,
        error_details=json.dumps(errors) if errors else None,
    )

    return success_rows, error_rows, errors


def generate_csv_report(queryset) -> str:
    """Generate CSV string from a Result queryset."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Roll Number', 'Name', 'Subject Code', 'Subject',
                     'Semester', 'Marks', 'Grade', 'Pass/Fail', 'Batch'])
    for r in queryset.select_related('student', 'subject', 'batch', 'student__profile'):
        writer.writerow([
            r.student.profile.roll_number,
            r.student.get_full_name(),
            r.subject.code,
            r.subject.name,
            r.semester,
            r.marks_obtained,
            r.grade,
            'Pass' if r.is_pass else 'Fail',
            r.batch.name,
        ])
    return output.getvalue()
