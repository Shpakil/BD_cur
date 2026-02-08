# scooter_rental/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from homepage import views as homepage_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', homepage_views.home, name='home'),
    path('users/', include('users.urls')),
    path('rentals/', include('rentals.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)