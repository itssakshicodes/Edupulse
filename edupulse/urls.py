"""
EduPulse URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('core:dashboard'), name='home'),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('results/', include('results.urls', namespace='results')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('core/', include('core.urls', namespace='core')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
