# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, UserLoginForm


def register_view(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('user_dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Вход в систему"""
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                # Проверяем роль и перенаправляем
                if user.userprofile.is_admin:
                    return redirect('/admin/')
                else:
                    return redirect('user_dashboard')
            else:
                messages.error(request, 'Неверные учетные данные')
    else:
        form = UserLoginForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """Выход из системы"""
    logout(request)
    return redirect('home')


@login_required
def user_dashboard(request):
    """Личный кабинет пользователя"""
    # Проверяем, что пользователь не администратор
    if request.user.userprofile.is_admin:
        return redirect('/admin/')

    # Получаем активную аренду пользователя
    from rentals.models import Rental
    active_rental = Rental.objects.filter(
        user=request.user,
        status='active'
    ).first()

    context = {
        'user': request.user,
        'active_rental': active_rental,
        'balance': request.user.userprofile.balance,
    }
    return render(request, 'users/dashboard.html', context)