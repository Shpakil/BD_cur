from django.db import models

class Station(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название станции")
    address = models.CharField(max_length=255, verbose_name="Адрес")
    capacity = models.IntegerField(verbose_name="Вместимость")

    def __str__(self):
        return self.name

class Scooter(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('rented', 'В аренде'),
        ('charging', 'На зарядке'),
    ]
    serial_number = models.CharField(max_length=50, unique=True)
    current_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, related_name='scooters')
    battery_charge = models.IntegerField(default=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')

    def __str__(self):
        return f"Самокат {self.serial_number} ({self.battery_charge}%)"