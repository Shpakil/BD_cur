from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Avg


# 1. Технические характеристики
class TechSpecs(models.Model):
    weight = models.FloatField("Вес (кг)")
    max_speed = models.IntegerField("Максимальная скорость (км/ч)")
    country = models.CharField("Страна производства", max_length=100, default="Китай")

    def __str__(self):
        return f"{self.max_speed} км/ч, {self.weight} кг ({self.country})"


# 2. Модель самоката
class ScooterModel(models.Model):
    name = models.CharField("Название модели", max_length=100)
    specs = models.OneToOneField(TechSpecs, on_delete=models.CASCADE, verbose_name="Тех. характеристики")

    def __str__(self):
        return self.name


# 3. Станция
class Station(models.Model):
    name = models.CharField("Название", max_length=100)
    address = models.CharField("Адрес", max_length=255)
    coordinates = models.CharField("Координаты", max_length=100)
    max_capacity = models.IntegerField("Максимальная вместимость")

    def __str__(self):
        return self.name


# 4. Самокат
class Scooter(models.Model):
    STATUS_CHOICES = [
        ('available', 'Доступен'),
        ('rented', 'В аренде'),
        ('maintenance', 'На обслуживании'),
    ]

    serial_number = models.CharField("Серийный номер", max_length=50, unique=True)
    mileage = models.FloatField("Пробег (км)", default=0.0)
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='available')

    model = models.ForeignKey(ScooterModel, on_delete=models.CASCADE, verbose_name="Модель")
    current_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True,
                                        verbose_name="Текущая станция")

    def __str__(self):
        return f"{self.serial_number} ({self.status})"

    def get_avg_rating(self):
        # Импорт внутри метода, чтобы избежать кругового импорта
        from .models import Review
        avg = Review.objects.filter(scooter=self).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else "Новый"

# 5. Батарея
class Battery(models.Model):
    capacity = models.IntegerField("Емкость (mAh)")
    status = models.CharField("Статус", max_length=50)
    end_warranty_date = models.DateField("Конец гарантийного срока")

    # Связь 1 к 1 с самокатом (установлена в самокат)
    scooter = models.OneToOneField(Scooter, on_delete=models.CASCADE, related_name='battery', verbose_name="Самокат")

    def __str__(self):
        return f"Батарея {self.capacity} mAh"


# 6. Техническое обслуживание
class TechService(models.Model):
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE)
    service_type = models.CharField("Тип обслуживания", max_length=100)
    executor = models.CharField("Исполнитель", max_length=100)
    date = models.DateField("Дата", auto_now_add=True)


# 7. Промокод / Акция
class Promo(models.Model):
    code = models.CharField(max_length=20, unique=True, verbose_name="Промокод")
    discount_percent = models.PositiveIntegerField(default=10, verbose_name="Скидка (%)")
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    expiry_date = models.DateField(null=True, blank=True, verbose_name="Срок действия")

    def __str__(self):
        return f"{self.code} (-{self.discount_percent}%)"


# 8. Аренда
class Rental(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    scooter = models.ForeignKey(Scooter, on_delete=models.CASCADE, verbose_name="Самокат")
    promo = models.ForeignKey(Promo, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Промокод")

    start_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, related_name='start_rentals')
    end_station = models.ForeignKey(Station, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='end_rentals')

    start_time = models.DateTimeField("Время начала", auto_now_add=True)
    end_time = models.DateTimeField("Время конца", null=True, blank=True)

    total_cost = models.DecimalField("Итоговая сумма", max_digits=10, decimal_places=2, null=True, blank=True)
    def __str__(self):
        return f"Аренда {self.id} - {self.user}"


# Профиль пользователя с балансом
class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField("Баланс", max_digits=10, decimal_places=2, default=500.00) # Дарим 500р при регистрации

    def __str__(self):
        return f"Профиль {self.user.username}"
class Technician(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='technician_profile', # Через это имя будем обращаться к данным техника
        verbose_name="Пользователь"
    )
    assigned_station = models.ForeignKey(
        'Station',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Закрепленная станция"
    )
    is_active_on_shift = models.BooleanField("На смене", default=True)

    class Meta:
        verbose_name = "Техник"
        verbose_name_plural = "Техники"

    def __str__(self):
        return f"Техник {self.user.username} - {self.assigned_station.name if self.assigned_station else 'Без станции'}"


# Автоматическое создание профиля при создании пользователя
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

# Обновим модель Payment (добавим связь с юзером для истории)
class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь", null=True)
    rental = models.OneToOneField('Rental', on_delete=models.CASCADE, verbose_name="Аренда")
    amount = models.DecimalField("Сумма", max_digits=10, decimal_places=2)
    date = models.DateTimeField("Дата", auto_now_add=True)
    method = models.CharField("Способ оплаты", max_length=50, default="С баланса")

    def __str__(self):
        return f"Платеж {self.id} за аренду {self.rental.id}"


# 10. Отзыв
class Review(models.Model):
    scooter = models.ForeignKey('Scooter', on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    text = models.TextField("Отзыв")
    rating = models.PositiveIntegerField("Оценка (1-5)")

    def __str__(self):
        return f"Отзыв к аренде {self.rental.id}"

from django.db.models.signals import post_save, post_delete

# Когда создаем или обновляем Техника — даем права персонала (is_staff)
@receiver(post_save, sender=Technician)
def sync_staff_status_on_save(sender, instance, **kwargs):
    if not instance.user.is_staff:
        instance.user.is_staff = True
        instance.user.save()

# Когда удаляем запись из Техников — забираем права персонала
@receiver(post_delete, sender=Technician)
def sync_staff_status_on_delete(sender, instance, **kwargs):
    if instance.user.is_staff:
        instance.user.is_staff = False
        instance.user.save()

@receiver(post_save, sender=Scooter)
def auto_create_battery(sender, instance, created, **kwargs):
    if created:
        Battery.objects.create(
            scooter=instance,
            capacity=100,
            status="Новая",
            end_warranty_date=timezone.now().date() + timezone.timedelta(days=365)
        )