from django.db import models
from django.conf import settings
from datetime import timedelta


class Membership(models.Model):
    """User membership with credits for shooting nights"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    credits_remaining = models.IntegerField(default=20)
    is_active = models.BooleanField(default=True)
    amount_paid = models.FloatField(default=100.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'memberships_membership'
        ordering = ['-created_at']
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'

    def __str__(self):
        return f'{self.user.email} - {self.start_date.date()} to {self.end_date.date()}'


class CreditPurchase(models.Model):
    """Purchase of additional credits by a member"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='credit_purchases'
    )
    credits_purchased = models.IntegerField()
    amount_paid = models.FloatField()
    purchase_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'memberships_creditpurchase'
        ordering = ['-purchase_date']
        verbose_name = 'Credit Purchase'
        verbose_name_plural = 'Credit Purchases'

    def __str__(self):
        return f'{self.user.email} - {self.credits_purchased} credits'
