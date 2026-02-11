from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('rent/<int:scooter_id>/', views.start_rent, name='start_rent'),
    path('my_rentals/', views.my_rentals, name='my_rentals'),
    path('finish/<int:rental_id>/', views.finish_rent, name='finish_rent'),
    path('payment/<int:rental_id>/', views.payment_page, name='payment_page'),
    path('tech/', views.tech_dashboard, name='tech_dashboard'),
    path('tech/status/<int:scooter_id>/', views.change_status, name='change_status'),
    path('station/<int:station_id>/', views.station_detail, name='station_detail'),
    path('review/<int:rental_id>/', views.leave_review, name='leave_review'),
]
