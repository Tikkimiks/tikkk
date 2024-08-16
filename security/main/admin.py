from django.contrib import admin

from .forms import MemberBrigadeForm, ServiceRequestForm, ServiceRequestAdminForm
from .models import *
from django.contrib import messages
from django.core.exceptions import ValidationError


class BrigadeAdmin(admin.ModelAdmin):
    list_display = ('id_brigade', 'name_brigade', 'chief', 'member_count')


class TariffAdmin(admin.ModelAdmin):
    list_display = ('duration', 'price')


class StatusAdmin(admin.ModelAdmin):
    list_display = ['id_status', 'name_status']


class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name_service', 'description', 'base_price', 'alarm_system_discount', 'category']
    search_fields = ['name_service', 'category__name']
    list_filter = ['category']


class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name']


class AreaAdmin(admin.ModelAdmin):
    list_display = ['id_area', 'name_area']


class ContractAdmin(admin.ModelAdmin):
    list_display = ('id_contract', 'name_contract', 'user', 'brigade', 'service', 'area')


class ReportAdmin(admin.ModelAdmin):
    list_display = ('date', 'number', 'description',)


class MemberBrigadeAdmin(admin.ModelAdmin):
    list_display = ('id_member_brigade', 'user', 'brigade', 'experience')
    form = MemberBrigadeForm


class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('id_schedule', 'start', 'end', 'brigade', 'assigned_member')


class ScheduleMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date', 'brigade')


class ScheduleEntryAdmin(admin.ModelAdmin):
    list_display = ('start', 'brigade', 'service_request', 'task_description')
    list_filter = ('start', 'brigade', 'service_request',)
    search_fields = ('start', 'task_description')

    def get_brigade(self, obj):
        return obj.brigade.name_brigade

    get_brigade.short_description = 'Brigade'

    def get_service_request(self, obj):
        return obj.service_request.name_service

    get_service_request.short_description = 'Service Request'


class ReceiptAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'date_receipt', 'total_amount', 'services')


class ContactAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'email', 'message')


class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'service', 'assigned_team', 'status', 'user')
    form = ServiceRequestAdminForm


admin.site.register(ServiceRequest, ServiceRequestAdmin)
admin.site.register(Schedule, ScheduleAdmin)
admin.site.register(ScheduleEntry, ScheduleEntryAdmin)
admin.site.register(ScheduleMember, ScheduleMemberAdmin)
admin.site.register(Tariff, TariffAdmin)
admin.site.register(Brigade, BrigadeAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Service, ServiceAdmin)
admin.site.register(ServiceCategory, ServiceCategoryAdmin)
admin.site.register(Area, AreaAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(Contact, ContactAdmin)
admin.site.register(Report, ReportAdmin)
admin.site.register(MemberBrigade, MemberBrigadeAdmin)
admin.site.register(Receipt, ReceiptAdmin)
