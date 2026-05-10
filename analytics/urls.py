from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Dashboards
    path('institution/',      views.institution_dashboard, name='institution'),
    path('subjects/',         views.subject_dashboard,     name='subjects'),
    path('student/',          views.student_dashboard,     name='student'),

    # JSON chart data endpoints (AJAX)
    path('chart/pass-fail/',          views.chart_pass_fail,          name='chart_pass_fail'),
    path('chart/grade-distribution/', views.chart_grade_distribution, name='chart_grade_distribution'),
    path('chart/semester-trend/',     views.chart_semester_trend,     name='chart_semester_trend'),
    path('chart/subject-comparison/', views.chart_subject_comparison, name='chart_subject_comparison'),
    path('chart/scatter/',            views.chart_scatter,            name='chart_scatter'),
    path('chart/student-trend/',      views.chart_student_trend,      name='chart_student_trend'),
]
