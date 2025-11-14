from django.contrib import admin
from .models import Membership, CreditPurchase


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'credits_remaining', 'is_active', 'amount_paid')
    list_filter = ('is_active', 'start_date', 'end_date')
    search_fields = ('user__email', 'user__name')
    readonly_fields = ('created_at', 'updated_at', 'start_date', 'shooting_attendance_list')
    fieldsets = (
        (None, {'fields': ('user', 'end_date', 'credits_remaining', 'is_active', 'amount_paid')}),
        ('Dates', {'fields': ('start_date', 'created_at', 'updated_at')}),
        ('Shooting History', {'fields': ('shooting_attendance_list',), 'classes': ('wide',)}),
    )
    
    class Media:
        css = {
            'all': ('admin/css/hide_shooting_label.css',)
        }

    def shooting_attendance_list(self, obj):
        """Display list of shooting nights attended"""
        if not obj.pk:
            return "Save membership to see shooting history"
        
        from shooting.models import ShootingAttendance
        from django.utils.html import format_html
        from django.utils.safestring import mark_safe
        
        attendances = ShootingAttendance.objects.filter(user=obj.user).select_related('shooting_night').order_by('-shooting_night__date')
        
        if not attendances:
            return format_html('<p style="color: #666; font-style: italic;">No shooting nights attended yet</p>')
        
        total = attendances.count()
        
        html = '<style>.field-shooting_attendance_list label { display: none !important; }</style>'
        html += f'<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #417690;">'
        html += f'<p style="margin: 0 0 15px 0; font-size: 14px; color: #417690; font-weight: 600;">📊 Total Visits: {total}</p>'
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 10px;">'
        
        for attendance in attendances:
            location_icons = {'Hall': '🏛️', 'Meadow': '🌿', 'Woods': '🌲'}
            icon = location_icons.get(attendance.shooting_night.location, '📍')
            
            html += f'''
            <div style="background: white; padding: 12px; border-radius: 6px; border: 1px solid #dee2e6; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="font-size: 13px; font-weight: 600; color: #212529; margin-bottom: 4px;">
                    📅 {attendance.shooting_night.date}
                </div>
                <div style="font-size: 12px; color: #6c757d;">
                    {icon} {attendance.shooting_night.get_location_display()}
                </div>
            </div>
            '''
        
        html += '</div></div>'
        return mark_safe(html)
    
    shooting_attendance_list.short_description = ''


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
