from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings

from .models import Membership, CreditPurchase
from .forms import CreditPurchaseForm


@login_required
def dashboard(request):
    """Unified member dashboard showing membership and credits"""
    membership = request.user.memberships.filter(is_active=True).first()
    recent_purchases = request.user.credit_purchases.all().order_by('-purchase_date')[:5]

    context = {
        'membership': membership,
        'recent_purchases': recent_purchases,
        'credit_cost': settings.CREDIT_COST,
    }
    return render(request, 'memberships/dashboard.html', context)


@login_required
def purchase_credits(request):
    """Handle credit purchase"""
    if request.method == 'POST':
        form = CreditPurchaseForm(
            request.POST,
            credit_cost=settings.CREDIT_COST
        )
        if form.is_valid():
            credits = form.cleaned_data['credits']
            amount = credits * settings.CREDIT_COST

            # Create credit purchase record
            purchase = CreditPurchase.objects.create(
                user=request.user,
                credits_purchased=credits,
                amount_paid=amount
            )

            # Add credits to current membership
            membership = request.user.memberships.filter(is_active=True).first()
            if membership:
                membership.credits_remaining += credits
                membership.save()

            messages.success(
                request,
                f'Successfully purchased {credits} credits for €{amount}!'
            )
            return redirect('memberships:dashboard')
    else:
        form = CreditPurchaseForm(credit_cost=settings.CREDIT_COST)

    context = {
        'form': form,
        'credit_cost': settings.CREDIT_COST,
    }
    return render(request, 'memberships/purchase_credits.html', context)
