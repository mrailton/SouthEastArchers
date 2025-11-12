from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from .forms import LoginForm, RegistrationForm
from .models import User
from memberships.models import Membership


@require_http_methods(['GET', 'POST'])
def login_view(request):
    """Handle user login with email"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                next_page = request.GET.get('next')
                return redirect(next_page) if next_page else redirect('core:dashboard')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(['GET', 'POST'])
def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('core:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Create initial membership
            membership = Membership.objects.create(
                user=user,
                end_date=timezone.now() + timedelta(days=365),
                credits_remaining=20,
                amount_paid=100.0
            )

            messages.success(
                request,
                'Registration successful! Your membership includes 20 shooting credits.'
            )

            # Log user in
            login(request, user)
            return redirect('memberships:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/register.html', {'form': form})


@login_required
@require_http_methods(['GET'])
def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('core:index')
