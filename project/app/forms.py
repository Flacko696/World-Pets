from decimal import Decimal

from django import forms

from .models import AnimalSpecies, Doctor

GENDERS = [('Самец', 'Самец'), ('Самка', 'Самка')]


class AppointmentForm(forms.Form):
    full_name = forms.CharField(label='ФИО владельца', max_length=150)
    phone = forms.CharField(
        label='Телефон', max_length=20,
        widget=forms.TextInput(attrs={'type': 'tel', 'placeholder': '+7 (902) 111-22-33'}),
    )
    email = forms.EmailField(label='Email (необязательно)', required=False)
    pet_name = forms.CharField(label='Кличка питомца', max_length=100)
    species = forms.ModelChoiceField(
        label='Вид животного', queryset=AnimalSpecies.objects.all(), empty_label='Выберите вид',
    )
    birth_date = forms.DateField(
        label='Дата рождения питомца', input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )
    gender = forms.ChoiceField(label='Пол', choices=GENDERS)
    weight = forms.DecimalField(
        label='Вес, кг', max_digits=5, decimal_places=2,
        min_value=Decimal('0.1'), max_value=Decimal('200'),
    )
    doctor = forms.ModelChoiceField(
        label='Врач', queryset=Doctor.objects.all(), empty_label='Выберите врача',
    )
    appointment_date = forms.DateField(
        label='Дата приёма', input_formats=['%Y-%m-%d'],
        widget=forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
    )
    appointment_time = forms.TimeField(
        label='Время приёма (с 9:00 до 21:00)',
        widget=forms.TimeInput(attrs={'type': 'time'}, format='%H:%M'),
    )
    complaints = forms.CharField(
        label='Жалобы (необязательно)', max_length=500, required=False,
        widget=forms.Textarea(attrs={'rows': 4}),
    )
class HomeVisitForm(AppointmentForm):
    # те же поля, что в обычной записи, плюс адрес; врач необязателен
    address = forms.CharField(
        label='Адрес визита', max_length=300,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Улица, дом, квартира, подъезд, этаж'}),
    )
    doctor = forms.ModelChoiceField(
        label='Врач (необязательно)', queryset=Doctor.objects.all(),
        required=False, empty_label='Любой свободный врач',
    )

    # порядок полей: адрес сразу после телефона
    field_order = [
        'full_name', 'phone', 'address', 'email', 'pet_name', 'species',
        'birth_date', 'gender', 'weight', 'doctor',
        'appointment_date', 'appointment_time', 'complaints',
    ]

    def save(self):
        appointment = super().save()                 # создаём владельца, питомца и приём как обычно
        appointment.status = 'Вызов на дом'          # помечаем, что это вызов
        appointment.save()
        owner = appointment.pet.owner
        owner.address = self.cleaned_data['address'] # сохраняем адрес владельца
        owner.save()
        return appointment