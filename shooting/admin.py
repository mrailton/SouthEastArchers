from django.contrib import admin
from .models import ShootingNight, ShootingAttendance


class ShootingAttendanceInline(admin.TabularInline):
    model = ShootingAttendance
    extra = 0
    fields = ('user', 'recorded_at')
    readonly_fields = ('recorded_at',)


@admin.register(ShootingNight)
class ShootingNightAdmin(admin.ModelAdmin):
    list_display = ('date', 'location', 'created_by', 'attendees_count', 'created_at')
    list_filter = ('date', 'location', 'created_at')
    search_fields = ('notes',)
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('date', 'location', 'notes')}),
        ('Metadata', {'fields': ('created_by', 'created_at', 'updated_at')}),
    )
    inlines = [ShootingAttendanceInline]

    def attendees_count(self, obj):
        return obj.attendees.count()
    attendees_count.short_description = 'Attendees'

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
