from django.db import models
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class ShootingNight(models.Model):
    """Shooting night events where members attend and use credits"""

    LOCATION_CHOICES = [
        ('hall', 'Hall'),
        ('meadow', 'Meadow'),
        ('woods', 'Woods'),
    ]

    date = models.DateField()
    location = models.CharField(max_length=50, choices=LOCATION_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_shooting_nights'
    )
    attendees = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='ShootingAttendance',
        related_name='attended_shooting_nights'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'shooting_shootingnight'
        ordering = ['-date']
        verbose_name = 'Shooting Night'
        verbose_name_plural = 'Shooting Nights'

    def __str__(self):
        return f'Shooting Night - {self.date} ({self.location})'


class ShootingAttendance(models.Model):
    """Through model for ShootingNight to User attendance with credit deduction"""

    shooting_night = models.ForeignKey(
        ShootingNight,
        on_delete=models.CASCADE,
        related_name='attendance_records'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    credits_deducted = models.IntegerField(default=1)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shooting_attendance'
        unique_together = ('shooting_night', 'user')
        verbose_name = 'Shooting Attendance'
        verbose_name_plural = 'Shooting Attendances'

    def __str__(self):
        return f'{self.user.email} - {self.shooting_night.date}'


@receiver(post_save, sender=ShootingAttendance)
def deduct_credits_on_attendance(sender, instance, created, **kwargs):
    """Automatically deduct credits when attendance is created"""
    if created:
        membership = instance.user.current_membership
        if membership and membership.credits_remaining >= instance.credits_deducted:
            membership.credits_remaining -= instance.credits_deducted
            membership.save()


@receiver(post_delete, sender=ShootingAttendance)
def refund_credits_on_delete(sender, instance, **kwargs):
    """Refund credits when attendance is deleted"""
    membership = instance.user.current_membership
    if membership:
        membership.credits_remaining += instance.credits_deducted
        membership.save()
