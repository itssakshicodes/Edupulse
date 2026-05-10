from django.contrib import admin
from .models import Result, Subject, Batch, UploadLog

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display  = ['code', 'name', 'department', 'semester', 'max_marks', 'pass_marks']
    list_filter   = ['department', 'semester']
    search_fields = ['code', 'name']

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display  = ['name', 'department', 'start_year', 'end_year']
    list_filter   = ['department']

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display  = ['student', 'subject', 'semester', 'marks_obtained', 'grade', 'is_pass', 'upload_date']
    list_filter   = ['grade', 'is_pass', 'semester']
    search_fields = ['student__username', 'subject__code']

@admin.register(UploadLog)
class UploadLogAdmin(admin.ModelAdmin):
    list_display  = ['file_name', 'uploaded_by', 'status', 'total_rows', 'success_rows', 'error_rows', 'uploaded_at']
    list_filter   = ['status']
