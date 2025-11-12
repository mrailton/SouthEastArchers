"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.http import JsonResponse

def health_check(request):
    """Simple health check endpoint for container orchestration."""
    return JsonResponse({"status": "healthy"}, status=200)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),

    # App URLs
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('member/', include('memberships.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
