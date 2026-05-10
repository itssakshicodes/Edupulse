from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    # Upload
    path('upload/',          views.upload_results, name='upload'),
    path('upload/logs/',     views.upload_logs,    name='upload_logs'),
    # CRUD
    path('',                 views.result_list,    name='result_list'),
    path('add/',             views.result_create,  name='result_create'),
    path('<int:pk>/edit/',   views.result_edit,    name='result_edit'),
    path('<int:pk>/delete/', views.result_delete,  name='result_delete'),
    # Export
    path('export/csv/',      views.export_csv,     name='export_csv'),
    path('export/pdf/',      views.export_pdf,     name='export_pdf'),
    # Subjects
    path('subjects/',              views.subject_list,   name='subject_list'),
    path('subjects/add/',          views.subject_create, name='subject_create'),
    path('subjects/<int:pk>/edit/', views.subject_edit,  name='subject_edit'),
    # Batches
    path('batches/',         views.batch_list,   name='batch_list'),
    path('batches/add/',     views.batch_create, name='batch_create'),
    # AJAX
    path('ajax/subjects/',   views.ajax_subjects, name='ajax_subjects'),
]
