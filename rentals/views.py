# rentals/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from .models import Station, Scooter, Rental
from .forms import StationSelectForm, ScooterSelectForm, RentalReturnForm


@login_required
def select_station(request):
    """Выбор станции для аренды"""
    # Проверяем, что у пользователя нет активной аренды
    active_rental = Rental.objects.filter(user=request.user, status='active').first()
    if active_rental:
        messages.warning(request, 'У вас уже есть активная аренда')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = StationSelectForm(request.POST)
        if form.is_valid():
            station = form.cleaned_data['station']
            request.session['selected_station_id'] = station.id
            return redirect('select_scooter')
    else:
        form = StationSelectForm()

    return render(request, 'rentals/select_station.html', {'form': form})


@login_required
def select_scooter(request):
    """Выбор самоката на выбранной станции"""
    station_id = request.session.get('selected_station_id')
    if not station_id:
        return redirect('select_station')

    station = get_object_or_404(Station, id=station_id)

    if request.method == 'POST':
        form = ScooterSelectForm(station_id, request.POST)
        if form.is_valid():
            scooter = form.cleaned_data['scooter']

            # Создаем аренду
            rental = Rental.objects.create(
                user=request.user,
                scooter=scooter,
                start_station=station
            )

            # Меняем статус самоката
            scooter.status = 'rented'
            scooter.station = None  # Убираем со станции
            scooter.save()

            messages.success(request, f'Самокат {scooter.scooter_id} арендован!')

            # Очищаем сессию
            if 'selected_station_id' in request.session:
                del request.session['selected_station_id']

            return redirect('user_dashboard')
    else:
        form = ScooterSelectForm(station_id)

    context = {
        'station': station,
        'form': form,
    }
    return render(request, 'rentals/select_scooter.html', context)


@login_required
def return_scooter(request):
    """Возврат самоката"""
    active_rental = Rental.objects.filter(user=request.user, status='active').first()
    if not active_rental:
        messages.error(request, 'У вас нет активной аренды')
        return redirect('user_dashboard')

    if request.method == 'POST':
        form = RentalReturnForm(request.POST)
        if form.is_valid():
            end_station = form.cleaned_data['end_station']

            # Завершаем аренду
            active_rental.end_station = end_station
            active_rental.end_time = timezone.now()
            active_rental.status = 'completed'
            active_rental.save()

            # Возвращаем самокат на станцию
            scooter = active_rental.scooter
            scooter.status = 'available'
            scooter.station = end_station

            # Уменьшаем заряд (симуляция использования)
            scooter.battery_level = max(0, scooter.battery_level - 30)
            scooter.save()

            # Рассчитываем стоимость
            cost = active_rental.calculate_cost()
            messages.success(request, f'Самокат возвращен. Стоимость: {cost} руб.')

            return redirect('payment', rental_id=active_rental.id)
    else:
        form = RentalReturnForm()

    context = {
        'rental': active_rental,
        'form': form,
    }
    return render(request, 'rentals/return_scooter.html', context)


@login_required
def process_payment(request, rental_id):
    """Обработка оплаты (упрощенная версия)"""
    rental = get_object_or_404(Rental, id=rental_id, user=request.user)

    if rental.is_paid:
        messages.info(request, 'Аренда уже оплачена')
        return redirect('user_dashboard')

    if request.method == 'POST':
        # Упрощенная оплата - просто отмечаем как оплаченную
        rental.is_paid = True
        rental.save()

        # Списание с баланса
        user_profile = request.user.userprofile
        if user_profile.balance >= rental.total_cost:
            user_profile.balance -= rental.total_cost
            user_profile.save()
            messages.success(request, f'Оплачено {rental.total_cost} руб.')
        else:
            messages.warning(request, 'Недостаточно средств на балансе')

        return redirect('user_dashboard')

    context = {
        'rental': rental,
    }
    return render(request, 'rentals/payment.html', context)


@login_required
def rental_history(request):
    """История аренд пользователя"""
    rentals = Rental.objects.filter(user=request.user).order_by('-start_time')
    return render(request, 'rentals/history.html', {'rentals': rentals})