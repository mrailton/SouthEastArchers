"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # App URLs
    path('', include('core.urls')),
    path('accounts/', include('accounts.urls')),
    path('member/', include('memberships.urls')),
]
