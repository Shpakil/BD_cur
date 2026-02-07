# rentals/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class Station(models.Model):
    """Станция самокатов"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    capacity = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)

    def available_scooters_count(self):
        return self.scooters.filter(status='available').count()

    def __str__(self):
        return f"{self.name} ({self.available_scooters_count()}/{self.capacity})"


class Scooter(models.Model):
    """Самокат"""
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('rented', 'Арендован'),
        ('maintenance', 'На обслуживании'),
        ('broken', 'Сломан'),
    ]

    scooter_id = models.CharField(max_length=20, unique=True)
    model = models.CharField(max_length=100)
    battery_level = models.IntegerField(default=100)  # в процентах
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    station = models.ForeignKey(Station, on_delete=models.SET_NULL,
                                null=True, blank=True, related_name='scooters')
    last_maintenance = models.DateField(null=True, blank=True)
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=5.00)

    def __str__(self):
        return f"{self.scooter_id} - {self.model} ({self.battery_level}%)"


class Rental(models.Model):
    """Аренда самоката"""
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE)
    start_station = models.ForeignKey(Station, on_delete=models.CASCADE,
                                      related_name='rentals_started')
    end_station = models.ForeignKey(Station, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='rentals_ended')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    total_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def duration_minutes(self):
        if self.end_time:
            duration = self.end_time - self.start_time
            return duration.total_seconds() // 60
        return 0

    def calculate_cost(self):
        """Расчет стоимости аренды"""
        if self.end_time:
            minutes = self.duration_minutes()
            hours = (minutes + 59) // 60  # округление вверх
            return hours * self.scooter.hourly_rate
        return 0

    def save(self, *args, **kwargs):
        if self.end_time and not self.total_cost:
            self.total_cost = self.calculate_cost()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Аренда #{self.id} - {self.user.username}"