from django.contrib import admin
from .models import Membership, CreditPurchase


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'credits_remaining', 'is_active', 'amount_paid')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('created_at', 'updated_at', 'start_date')
    fieldsets = (
        (None, {'fields': ('user', 'end_date', 'credits_remaining', 'is_active', 'amount_paid')}),
        ('Dates', {'fields': ('start_date', 'created_at', 'updated_at')}),
    )


@admin.register(CreditPurchase)
class CreditPurchaseAdmin(admin.ModelAdmin):
    list_display = ('user', 'credits_purchased', 'amount_paid', 'purchase_date')
    list_filter = ('purchase_date',)
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('purchase_date',)
    fieldsets = (
        (None, {'fields': ('user', 'credits_purchased', 'amount_paid')}),
        ('Date', {'fields': ('purchase_date',)}),
    )
