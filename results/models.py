"""
results/models.py
Core academic data models: Batch, Subject, Result.
Auto-calculates grades + pass/fail on save.
"""
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Batch(models.Model):
    """Represents a student cohort / year group."""
    name       = models.CharField(max_length=100)          # e.g. "2021-2025"
    department = models.CharField(max_length=100)
    start_year = models.PositiveIntegerField()
    end_year   = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Batches'
        unique_together = ('name', 'department')
        ordering = ['-start_year']

    def __str__(self):
        return f"{self.name} — {self.department}"


class Subject(models.Model):
    """A course/subject tied to a department and semester."""
    name        = models.CharField(max_length=150)
    code        = models.CharField(max_length=20, unique=True)
    department  = models.CharField(max_length=100)
    semester    = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    max_marks   = models.PositiveIntegerField(default=100)
    pass_marks  = models.PositiveIntegerField(default=40)
    credits     = models.PositiveSmallIntegerField(default=4)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['semester', 'name']

    def __str__(self):
        return f"{self.code} — {self.name} (Sem {self.semester})"


class Result(models.Model):
    """
    A single student result for one subject in one semester.
    Grade and pass/fail are computed automatically.
    """
    GRADE_CHOICES = [
        ('O',  'Outstanding (90-100)'),
        ('A+', 'Excellent (80-89)'),
        ('A',  'Very Good (70-79)'),
        ('B+', 'Good (60-69)'),
        ('B',  'Above Average (50-59)'),
        ('C',  'Average (40-49)'),
        ('F',  'Fail (< 40)'),
    ]

    student     = models.ForeignKey(User,    on_delete=models.CASCADE,  related_name='results')
    subject     = models.ForeignKey(Subject, on_delete=models.CASCADE,  related_name='results')
    batch       = models.ForeignKey(Batch,   on_delete=models.CASCADE,  related_name='results')
    semester    = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )
    marks_obtained = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    grade       = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    is_pass     = models.BooleanField(default=False)
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='uploaded_results'
    )
    upload_date = models.DateTimeField(auto_now_add=True)
    remarks     = models.TextField(blank=True, null=True)

    class Meta:
        # One result per student per subject per semester
        unique_together = ('student', 'subject', 'semester', 'batch')
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.student.username} | {self.subject.code} | Sem {self.semester} | {self.marks_obtained}"

    # ── Grade auto-calculation ───────────────────────────────────────────
    @staticmethod
    def calculate_grade(marks):
        """Return letter grade based on percentage marks."""
        if marks >= 90: return 'O'
        if marks >= 80: return 'A+'
        if marks >= 70: return 'A'
        if marks >= 60: return 'B+'
        if marks >= 50: return 'B'
        if marks >= 40: return 'C'
        return 'F'

    def save(self, *args, **kwargs):
        # Auto-set grade and pass/fail before saving
        self.grade   = self.calculate_grade(self.marks_obtained)
        self.is_pass = self.marks_obtained >= self.subject.pass_marks
        super().save(*args, **kwargs)

    def clean(self):
        if self.marks_obtained > self.subject.max_marks:
            raise ValidationError(
                f"Marks ({self.marks_obtained}) cannot exceed max marks ({self.subject.max_marks})."
            )

    @property
    def percentage(self):
        return round((self.marks_obtained / self.subject.max_marks) * 100, 2)


class UploadLog(models.Model):
    """Audit log for every CSV/Excel upload."""
    STATUS_CHOICES = [('success', 'Success'), ('partial', 'Partial'), ('failed', 'Failed')]

    uploaded_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    file_name      = models.CharField(max_length=255)
    uploaded_at    = models.DateTimeField(auto_now_add=True)
    total_rows     = models.IntegerField(default=0)
    success_rows   = models.IntegerField(default=0)
    error_rows     = models.IntegerField(default=0)
    status         = models.CharField(max_length=10, choices=STATUS_CHOICES, default='success')
    error_details  = models.TextField(blank=True, null=True)  # JSON string of errors

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.file_name} by {self.uploaded_by} — {self.status}"
