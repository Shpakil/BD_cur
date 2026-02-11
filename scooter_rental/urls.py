from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  # Импорт стандартных входов
from users.views import register  # Твоя функция регистрации

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),

    # ВОТ ЭТИ СТРОКИ ДОЛЖНЫ БЫТЬ ТУТ:
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('register/', register, name='register'),
]