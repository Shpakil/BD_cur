# rentals/admin.py
from django.contrib import admin
from .models import Station, Scooter, Rental

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ['name', 'address', 'available_scooters_count', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'address']

@admin.register(Scooter)
class ScooterAdmin(admin.ModelAdmin):
    list_display = ['scooter_id', 'model', 'battery_level', 'status', 'station', 'hourly_rate']
    list_filter = ['status', 'station']
    search_fields = ['scooter_id', 'model']
    list_editable = ['status', 'battery_level']

@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'scooter', 'start_time', 'end_time', 'status', 'is_paid']
    list_filter = ['status', 'is_paid', 'start_time']
    search_fields = ['user__username', 'scooter__scooter_id']