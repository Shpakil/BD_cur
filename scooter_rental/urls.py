from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Админка
    path('admin/', admin.site.urls),

    # 2. Твои приложения
    path('', include('homepage.urls')),        # Главная страница (пустой путь)
    path('rent/', include('rentals.urls')),    # Всё про аренду будет начинаться с /rent/
    path('users/', include('users.urls')),     # Всё про юзеров будет начинаться с /users/
]

# 3. Подключение медиа-файлов (картинок), чтобы они отображались в браузере
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)