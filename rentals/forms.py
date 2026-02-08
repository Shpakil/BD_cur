# rentals/forms.py
from django import forms
from .models import Scooter, Station, Rental


class StationSelectForm(forms.Form):
    """Форма выбора станции"""
    station = forms.ModelChoiceField(
        queryset=Station.objects.filter(is_active=True),
        label="Выберите станцию",
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class ScooterSelectForm(forms.Form):
    """Форма выбора самоката"""
    scooter = forms.ModelChoiceField(
        queryset=Scooter.objects.none(),  # Будет заполнен во view
        label="Выберите самокат",
        widget=forms.RadioSelect
    )

    def __init__(self, station_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if station_id:
            self.fields['scooter'].queryset = Scooter.objects.filter(
                station_id=station_id,
                status='available',
                battery_level__gte=20  # Минимальный заряд 20%
            )


class RentalReturnForm(forms.Form):
    """Форма возврата самоката"""
    end_station = forms.ModelChoiceField(
        queryset=Station.objects.filter(is_active=True),
        label="Станция возврата"
    )