import csv
import json
import math
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.db import transaction
from django.contrib import messages
from decimal import Decimal
from .models import Scooter, Rental, Payment, Station, ScooterModel, Profile, Battery, Promo
from .forms import ReviewForm, DepositForm
from django.http import HttpResponse, JsonResponse
from django.apps import apps
from django.contrib.auth.decorators import user_passes_test

# --- ЭКСПОРТ ДАННЫХ ---



@user_passes_test(lambda u: u.is_superuser)
def export_to_csv(request, model_name):
    try:
        model = apps.get_model('core', model_name)
    except LookupError:
        return HttpResponse("Модель не найдена", status=404)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{model_name}.csv"'

    writer = csv.writer(response)
    fields = [field.name for field in model._meta.fields]

    writer.writerow(fields)
    for obj in model.objects.all():
        writer.writerow([getattr(obj, field) for field in fields])

    return response


@user_passes_test(lambda u: u.is_superuser)
def export_to_json(request, model_name):
    try:
        model = apps.get_model('core', model_name)
    except LookupError:
        return HttpResponse("Модель не найдена", status=404)

    data = list(model.objects.values())

    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 4})
    response['Content-Disposition'] = f'attachment; filename="{model_name}.json"'

    return response
def export_scooters_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="scooters.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'Model', 'Status'])

    for s in Scooter.objects.all():
        model_name = s.model.name if s.model else "Нет модели"
        writer.writerow([s.id, model_name, s.status])
    return response


def export_scooters_json(request):
    data = [{
        'id': s.id,
        'model': s.model.name if s.model else None,
        'status': s.status
    } for s in Scooter.objects.all()]

    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 4})

    response['Content-Disposition'] = 'attachment; filename="scooters.json"'

    return response

# --- ПОЛЬЗОВАТЕЛЬСКИЙ ИНТЕРФЕЙС ---

def home(request):

    return render(request, 'core/home.html', {'stations': Station.objects.all()})


def station_detail(request, station_id):
    station = get_object_or_404(Station, id=station_id)
    scooters = Scooter.objects.filter(current_station=station, status='available')
    return render(request, 'core/station_detail.html', {'station': station, 'scooters': scooters})


def all_models_list(request):
    """Каталог моделей самокатов и их характеристик"""
    return render(request, 'core/all_models.html', {'models': ScooterModel.objects.all()})


# --- АРЕНДА И ПОЕЗДКИ ---

@login_required
def start_rent(request, scooter_id):
    scooter = get_object_or_404(Scooter, id=scooter_id)

    # 1. Проверка на доступность
    if scooter.status != 'available':
        messages.error(request, 'Этот самокат уже занят или находится на обслуживании.')
        return redirect('home')

    # 2. Проверка наличия батареи
    if not hasattr(scooter, 'battery'):
        messages.error(request, 'Этот самокат не готов к поездке (отсутствует батарея).')
        return redirect('home')

    # 3. Проверка заряда
    if scooter.battery.capacity < 10:
        messages.error(request, 'Заряд самоката слишком низкий для начала аренды.')
        return redirect('home')

    # 4. Проверка баланса
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if profile.balance < 100:
        messages.warning(request, f'Недостаточно средств. Ваш баланс: {profile.balance} ₽. Нужно минимум 100 ₽.')
        return redirect('home')

    # 5. Проверка на наличие активной поездки
    if Rental.objects.filter(user=request.user, end_time__isnull=True).exists():
        messages.info(request, 'У вас уже есть активная поездка! Сначала завершите её.')
        return redirect('my_rentals')

    # Если всё проверки пройдены — начинаем аренду
    Rental.objects.create(
        user=request.user,
        scooter=scooter,
        start_station=scooter.current_station
    )

    # Обновляем статус самоката
    scooter.status = 'rented'
    scooter.current_station = None
    scooter.save()

    messages.success(request, 'Поездка успешно начата! Приятного пути.')
    return redirect('my_rentals')


@transaction.atomic
@login_required
def finish_rent(request, rental_id):

    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    if request.method == 'POST':
        station_id = request.POST.get('end_station')
        promo_code = request.POST.get('promo_code', '').strip()
        end_station = get_object_or_404(Station, id=station_id)

        # Устанавливаем время финиша и станцию прибытия
        rental.end_time = timezone.now()
        rental.end_station = end_station

        # 1. Расчет базовой стоимости
        duration = rental.end_time - rental.start_time
        minutes = max(1, math.ceil(duration.total_seconds() / 60))
        base_price = minutes * 5  # 5 рублей в минуту

        # 2. Логика ПРОМОКОДА
        discount = 0
        if promo_code:
            try:
                promo = Promo.objects.get(code__iexact=promo_code, is_active=True)
                if promo.expiry_date is None or promo.expiry_date >= timezone.now().date():
                    discount = (base_price * promo.discount_percent) / 100
                    messages.success(request, f"Применен промокод: -{promo.discount_percent}%")
                else:
                    messages.error(request, "Срок действия промокода истек.")
            except Promo.DoesNotExist:
                messages.error(request, "Неверный промокод.")

        total_price = Decimal(str(max(0, base_price - discount)))
        rental.total_cost = total_price

        # 3. Работа с балансом пользователя
        profile = request.user.profile
        profile.balance -= total_price
        profile.save()

        # 4. ОБНОВЛЕНИЕ САМОКАТА
        scooter = rental.scooter
        scooter.current_station = end_station
        scooter.status = 'available'
        scooter.save()

        # 5. Сохранение поездки и создание чека
        rental.save()
        Payment.objects.create(
            user=request.user,
            rental=rental,
            amount=total_price,
            method='balance'
        )

        messages.success(request, f"Поездка завершена. Списано: {total_price} ₽. Самокат оставлен на: {end_station.name}")
        return redirect('leave_review', rental_id=rental.id)


    return redirect('profile')

@login_required
def my_rentals(request):
    """История поездок и активные аренды"""
    rentals = Rental.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'core/my_rentals.html', {
        'rentals': rentals,
        'stations': Station.objects.all()
    })


# --- ЛИЧНЫЙ КАБИНЕТ И ФИНАНСЫ ---
@login_required
def user_profile(request):
    """Профиль пользователя: баланс и история поездок"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    rentals = Rental.objects.filter(user=request.user).order_by('-start_time')
    payments = Payment.objects.filter(user=request.user).order_by('-date')
    return render(request, 'core/user_profile.html', {
        'rentals': rentals,
        'payments': payments
    })


@login_required
def top_up_balance(request):
    """Пополнение виртуального баланса"""
    if request.method == 'POST':
        form = DepositForm(request.POST)
        if form.is_valid():
            amount = form.cleaned_data['amount']
            profile = request.user.profile
            profile.balance += amount
            profile.save()
            messages.success(request, f"Баланс пополнен на {amount} ₽!")
            return redirect('user_profile')
    else:
        form = DepositForm()
    return render(request, 'core/top_up.html', {'form': form})


@login_required
def view_receipt(request, payment_id):
    """Просмотр чека по транзакции"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    return render(request, 'core/receipt.html', {'payment': payment})


# --- ОТЗЫВЫ ---

@login_required
def leave_review(request, rental_id):
    """Оставить отзыв после поездки"""
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    # Проверка, не оставлен ли отзыв ранее
    if hasattr(rental, 'review'):
        messages.info(request, "Отзыв о данной поездке уже существует.")
        return redirect('my_rentals')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.rental = rental
            review.user = request.user
            review.scooter = rental.scooter
            review.save()
            messages.success(request, "Спасибо за оценку!")
            return redirect('my_rentals')

    return render(request, 'core/leave_review.html', {
        'form': ReviewForm(),
        'rental': rental
    })

# --- ПАНЕЛЬ ТЕХНИКА ---

def is_technician(user):
    return user.is_authenticated and hasattr(user, 'technician_profile')


@user_passes_test(is_technician)
def tech_dashboard(request):
    """Кабинет техника: показывает самокаты в зависимости от привязки к станции"""
    try:
        tech_profile = request.user.technician_profile  # related_name из твоей модели
        assigned_station = tech_profile.assigned_station
    except:
        tech_profile = None
        assigned_station = None

    # Логика фильтрации:
    if assigned_station:
        # Если техник привязан к станции, показываем только её самокаты
        scooters = Scooter.objects.filter(current_station=assigned_station).order_by('id')
    else:
        # Если не привязан, показываем все
        scooters = Scooter.objects.all().order_by('id')

    return render(request, 'core/tech_dashboard.html', {
        'scooters': scooters,
        'tech_profile': tech_profile,
        'assigned_station': assigned_station
    })


@user_passes_test(is_technician)
def change_status(request, scooter_id):
    """Ручное управление статусом (ремонт/доступен)"""
    scooter = get_object_or_404(Scooter, id=scooter_id)
    if request.method == 'POST':
        scooter.status = request.POST.get('status')
        scooter.save()
    return redirect('tech_dashboard')


@user_passes_test(is_technician)
def change_status(request, scooter_id):
    if request.method == 'POST':
        scooter = get_object_or_404(Scooter, id=scooter_id)
        new_status = request.POST.get('status')

        scooter.status = new_status


        if new_status == 'available':
            if hasattr(scooter, 'battery'):
                # Если батарея есть — заряжаем
                scooter.battery.capacity = 100
                scooter.battery.save()
            else:
                # Если батареи почему-то нет — создаем новую
                Battery.objects.create(
                    scooter=scooter,
                    capacity=100,
                    status="Новая (после ТО)",
                    end_warranty_date=timezone.now().date() + timezone.timedelta(days=365)
                )
            messages.success(request, f"Самокат {scooter.serial_number} заряжен и готов к работе!")

        scooter.save()
    return redirect('tech_dashboard')