# rentals/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('select-station/', views.select_station, name='select_station'),
    path('select-scooter/', views.select_scooter, name='select_scooter'),
    path('return/', views.return_scooter, name='return_scooter'),
    path('payment/<int:rental_id>/', views.process_payment, name='payment'),
    path('history/', views.rental_history, name='rental_history'),
]