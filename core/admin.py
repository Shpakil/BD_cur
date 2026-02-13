from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.apps import apps
from .models import (
    Scooter, Rental, Station, Profile, Technician,
    TechSpecs, ScooterModel, Battery, TechService,
    Promo, Payment, Review
)

User = get_user_model()

# --- БАЗОВЫЙ КЛАСС ДЛЯ ЭКСПОРТА ---
class ExportAdmin(admin.ModelAdmin):
    change_list_template = "admin/change_list.html"

    def changelist_view(self, request, extra_context=None):
        model_name = self.model.__name__.lower()
        extra_context = extra_context or {}
        extra_context['export_buttons'] = mark_safe(
            f'<div style="margin-bottom: 20px; padding: 10px; background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px;">'
            f'<strong>Выгрузить данные ({self.model._meta.verbose_name}): </strong>'
            f'<a class="button" style="background: #79aec8; color: white; padding: 5px 15px; margin-right: 10px; text-decoration: none; border-radius: 4px;" href="/export/csv/{model_name}/">CSV</a>'
            f'<a class="button" style="background: #417690; color: white; padding: 5px 15px; text-decoration: none; border-radius: 4px;" href="/export/json/{model_name}/">JSON</a>'
            f'</div>'
        )
        return super().changelist_view(request, extra_context=extra_context)

# --- 1. ПОЛЬЗОВАТЕЛИ И ПРОФИЛИ ---

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Баланс кошелька'

class MyUserAdmin(ExportAdmin, BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'get_balance', 'is_technician_role', 'is_staff')
    search_fields = ('username', 'email')

    def get_balance(self, obj):
        try:
            return f"{obj.profile.balance} ₽"
        except:
            return "0 ₽"
    get_balance.short_description = 'Баланс'

    def is_technician_role(self, obj):
        return hasattr(obj, 'technician_profile')
    is_technician_role.boolean = True
    is_technician_role.short_description = 'Сотрудник (Техник)'

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, MyUserAdmin)

# --- 2. ТРАНСПОРТ ---

@admin.register(Scooter)
class ScooterAdmin(ExportAdmin):
    list_display = ('id', 'status', 'current_station')
    list_filter = ('status', 'current_station')
    list_editable = ('status', 'current_station')

@admin.register(ScooterModel)
class ScooterModelAdmin(ExportAdmin):
    list_display = ('name', 'specs')

@admin.register(TechSpecs)
class TechSpecsAdmin(ExportAdmin):
    list_display = ('country', 'max_speed', 'weight')
    list_filter = ('country',)

@admin.register(Battery)
class BatteryAdmin(ExportAdmin):
    list_display = ('id',) # Оставил только id, чтобы не было ошибок полей

# --- 3. ЛОГИСТИКА И ФИНАНСЫ ---

@admin.register(Station)
class StationAdmin(ExportAdmin):
    list_display = ('name', 'address', 'max_capacity')
    search_fields = ('name', 'address')

@admin.register(Rental)
class RentalAdmin(ExportAdmin):
    list_display = ('id', 'user', 'scooter', 'total_cost')
    list_filter = ('scooter', 'user')

@admin.register(Payment)
class PaymentAdmin(ExportAdmin):
    list_display = ('id', 'user', 'amount', 'date', 'method')

# --- 4. ТЕХНИЧЕСКИЙ РАЗДЕЛ ---

@admin.register(Technician)
class TechnicianAdmin(ExportAdmin):
    list_display = ('user', 'assigned_station', 'is_active_on_shift')
    autocomplete_fields = ['user']

@admin.register(TechService)
class TechServiceAdmin(ExportAdmin):
    list_display = ('scooter', 'service_type', 'executor', 'date')

# --- 5. МАРКЕТИНГ И ОТЗЫВЫ ---

@admin.register(Review)
class ReviewAdmin(ExportAdmin):
    list_display = ('id', 'rating')

@admin.register(Promo)
class PromoAdmin(ExportAdmin):
    list_display = ('id',)