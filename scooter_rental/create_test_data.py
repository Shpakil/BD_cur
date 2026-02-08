#!/usr/bin/env python
"""
Скрипт для создания тестовых данных в базе данных.
Запуск: python create_test_data.py
"""

import os
import django
import random
from datetime import datetime, timedelta

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'scooter_rental.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import UserProfile
from rentals.models import Station, Scooter, Rental


def clear_database():
    """Очистка существующих данных (опционально)"""
    print("Очистка старых данных...")
    Rental.objects.all().delete()
    Scooter.objects.all().delete()
    Station.objects.all().delete()
    # Не удаляем пользователей, чтобы не удалить админа
    UserProfile.objects.filter(user__username__startswith='user').delete()
    User.objects.filter(username__startswith='user').delete()


def create_stations():
    """Создание станций самокатов"""
    print("Создание станций...")

    stations_data = [
        {
            'name': 'Центральная площадь',
            'address': 'г. Москва, Красная площадь, 1',
            'latitude': 55.7540,
            'longitude': 37.6201,
            'capacity': 15
        },
        {
            'name': 'ВДНХ',
            'address': 'г. Москва, проспект Мира, 119',
            'latitude': 55.8217,
            'longitude': 37.6383,
            'capacity': 12
        },
        {
            'name': 'Парк Горького',
            'address': 'г. Москва, ул. Крымский Вал, 9',
            'latitude': 55.7299,
            'longitude': 37.6031,
            'capacity': 10
        },
        {
            'name': 'Москва-Сити',
            'address': 'г. Москва, Пресненская наб., 8с1',
            'latitude': 55.7480,
            'longitude': 37.5393,
            'capacity': 8
        },
        {
            'name': 'МГУ',
            'address': 'г. Москва, Ленинские горы, 1',
            'latitude': 55.7030,
            'longitude': 37.5286,
            'capacity': 20
        }
    ]

    stations = []
    for data in stations_data:
        station, created = Station.objects.get_or_create(
            name=data['name'],
            defaults=data
        )
        stations.append(station)
        if created:
            print(f"  Создана станция: {station.name}")

    return stations


def create_scooters(stations):
    """Создание самокатов"""
    print("Создание самокатов...")

    scooter_models = [
        {'model': 'Xiaomi Mi Electric Scooter Pro 2', 'hourly_rate': 7.00},
        {'model': 'Ninebot MAX G30', 'hourly_rate': 8.00},
        {'model': 'Kugoo Kirin S3', 'hourly_rate': 6.50},
        {'model': 'Smart Balance Wheel 10S', 'hourly_rate': 5.50},
        {'model': 'Xiaomi Mi Electric Scooter 3', 'hourly_rate': 6.00},
    ]

    statuses = ['available', 'available', 'available', 'maintenance', 'available']

    scooters = []
    for i in range(1, 31):  # Создаем 30 самокатов
        model_data = random.choice(scooter_models)
        scooter_id = f'SC{i:03d}'

        # Распределяем по станциям
        station = random.choice(stations) if random.random() > 0.3 else None

        # Случайный статус (80% доступны)
        status = random.choices(
            ['available', 'rented', 'maintenance', 'broken'],
            weights=[0.8, 0.1, 0.07, 0.03]
        )[0]

        scooter, created = Scooter.objects.get_or_create(
            scooter_id=scooter_id,
            defaults={
                'model': model_data['model'],
                'battery_level': random.randint(20, 100),
                'status': status,
                'station': station if status == 'available' else None,
                'hourly_rate': model_data['hourly_rate'],
                'last_maintenance': datetime.now().date() - timedelta(days=random.randint(0, 30))
            }
        )

        scooters.append(scooter)
        if created:
            print(f"  Создан самокат: {scooter.scooter_id} ({scooter.model})")

    return scooters


def create_test_users():
    """Создание тестовых пользователей"""
    print("Создание тестовых пользователей...")

    test_users = [
        {'username': 'user1', 'email': 'user1@example.com', 'phone': '+79161234567', 'balance': 500.00},
        {'username': 'user2', 'email': 'user2@example.com', 'phone': '+79162345678', 'balance': 300.00},
        {'username': 'user3', 'email': 'user3@example.com', 'phone': '+79163456789', 'balance': 1000.00},
        {'username': 'user4', 'email': 'user4@example.com', 'phone': '+79164567890', 'balance': 150.00},
        {'username': 'user5', 'email': 'user5@example.com', 'phone': '+79165678901', 'balance': 750.00},
    ]

    users = []
    for user_data in test_users:
        # Проверяем, существует ли пользователь
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={'email': user_data['email']}
        )

        if created:
            # Устанавливаем пароль (для всех тестовых пользователей один пароль)
            user.set_password('password123')
            user.save()

            # Создаем/обновляем профиль
            profile, _ = UserProfile.objects.get_or_create(
                user=user,
                defaults={
                    'phone': user_data['phone'],
                    'balance': user_data['balance'],
                    'role': 'user'
                }
            )

            # Обновляем телефон и баланс
            profile.phone = user_data['phone']
            profile.balance = user_data['balance']
            profile.save()

            users.append(user)
            print(f"  Создан пользователь: {user.username} (пароль: password123)")
        else:
            users.append(user)
            print(f"  Пользователь {user.username} уже существует")

    return users


def create_test_rentals(users, scooters, stations):
    """Создание тестовых аренд"""
    print("Создание тестовых аренд...")

    # Создаем несколько завершенных аренд в прошлом
    for i in range(10):
        user = random.choice(users)
        scooter = random.choice([s for s in scooters if s.status == 'available'])
        start_station = random.choice(stations)

        # Случайная дата в прошлом
        start_time = datetime.now() - timedelta(days=random.randint(1, 30), hours=random.randint(1, 10))
        end_time = start_time + timedelta(hours=random.randint(1, 5))

        rental = Rental.objects.create(
            user=user,
            scooter=scooter,
            start_station=start_station,
            end_station=random.choice(stations),
            start_time=start_time,
            end_time=end_time,
            status='completed',
            is_paid=random.choice([True, False])
        )

        # Рассчитываем стоимость
        rental.total_cost = rental.calculate_cost()
        rental.save()

        print(f"  Создана аренда #{rental.id} для {user.username}")

    # Создаем несколько активных аренд
    for i in range(3):
        user = random.choice(users)
        scooter = random.choice([s for s in scooters if s.status == 'available'])
        start_station = random.choice(stations)

        # Меняем статус самоката
        scooter.status = 'rented'
        scooter.station = None
        scooter.save()

        rental = Rental.objects.create(
            user=user,
            scooter=scooter,
            start_station=start_station,
            status='active'
        )

        print(f"  Создана активная аренда #{rental.id} для {user.username}")


def create_admin_user():
    """Создание администратора (если нет)"""
    print("Проверка администратора...")

    try:
        # Проверяем, есть ли уже администратор
        admin_user = User.objects.get(username='admin')
        print(f"  Администратор уже существует: {admin_user.username}")
    except User.DoesNotExist:
        # Создаем администратора
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@scooter-rental.ru',
            password='admin123'
        )

        # Обновляем профиль
        admin_profile, _ = UserProfile.objects.get_or_create(user=admin_user)
        admin_profile.role = 'admin'
        admin_profile.phone = '+79998887766'
        admin_profile.balance = 0
        admin_profile.save()

        print(f"  Создан администратор: {admin_user.username} (пароль: admin123)")


def main():
    """Основная функция"""
    print("=" * 50)
    print("Создание тестовых данных для Scooter Rental")
    print("=" * 50)

    # Опционально: очистить базу данных
    # clear_database()  # Раскомментируйте, если хотите очистить старые данные

    # Создаем администратора
    create_admin_user()

    # Создаем станции
    stations = create_stations()

    # Создаем самокаты
    scooters = create_scooters(stations)

    # Создаем тестовых пользователей
    users = create_test_users()

    # Создаем тестовые аренды
    create_test_rentals(users, scooters, stations)

    # Выводим статистику
    print("\n" + "=" * 50)
    print("СТАТИСТИКА:")
    print(f"  Станций: {Station.objects.count()}")
    print(f"  Самокатов: {Scooter.objects.count()}")
    print(f"    - Доступно: {Scooter.objects.filter(status='available').count()}")
    print(f"    - Арендовано: {Scooter.objects.filter(status='rented').count()}")
    print(f"  Пользователей: {User.objects.count()}")
    print(f"  Администраторов: {UserProfile.objects.filter(role='admin').count()}")
    print(f"  Аренд: {Rental.objects.count()}")
    print(f"    - Активных: {Rental.objects.filter(status='active').count()}")
    print(f"    - Завершенных: {Rental.objects.filter(status='completed').count()}")
    print("=" * 50)
    print("\nТестовые данные успешно созданы!")
    print("\nДоступные учетные записи:")
    print("  Администратор: admin / admin123")
    print("  Пользователи: user1..user5 / password123")


if __name__ == '__main__':
    main()