from django.urls import path
from . import views

urlpatterns = [
    # Главная и списки
    path('', views.home, name='home'),
    path('models/', views.all_models_list, name='all_models_list'),
    path('station/<int:station_id>/', views.station_detail, name='station_detail'),

    # Аренда (запуск и завершение)
    path('rent/start/<int:scooter_id>/', views.start_rent, name='start_rent'),
    path('rent/finish/<int:rental_id>/', views.finish_rent, name='finish_rent'),
    path('my-rentals/', views.my_rentals, name='my_rentals'),

    # Личный кабинет и финансы
    path('profile/', views.user_profile, name='user_profile'),
    path('top-up/', views.top_up_balance, name='top_up_balance'),
    path('receipt/<int:payment_id>/', views.view_receipt, name='view_receipt'), # Это исправит NoReverseMatch
    path('review/<int:rental_id>/', views.leave_review, name='leave_review'),

    # Панель техника
    path('tech/', views.tech_dashboard, name='tech_dashboard'),
    path('tech/status/<int:scooter_id>/', views.change_status, name='change_status'),

    # Выгрузка данных
    path('export/csv/', views.export_scooters_csv, name='export_scooters_csv'),
    path('export/json/', views.export_scooters_json, name='export_scooters_json'),
    path('export/csv/<str:model_name>/', views.export_to_csv, name='export_csv'),
    path('export/json/<str:model_name>/', views.export_to_json, name='export_json'),
]