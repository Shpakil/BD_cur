from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    # Стандартные поля (username, password) уже есть в AbstractUser
    fio = models.CharField("ФИО", max_length=255)
    age = models.PositiveIntegerField("Возраст", null=True, blank=True)

    GENDER_CHOICES = [
        ('M', 'Мужской'),
        ('F', 'Женский'),
    ]
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES, blank=True)

    def __str__(self):
        return self.fio or self.username