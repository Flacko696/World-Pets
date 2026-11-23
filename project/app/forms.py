import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django import forms

from .models import AnimalSpecies, Appointment, Doctor, Feedback, Owner, Pet

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
    def save(self):
        data = self.cleaned_data
        owner, _ = Owner.objects.get_or_create(
            phone=data['phone'],
            defaults={'full_name': data['full_name'], 'email': data['email'] or None},
        )
        pet, _ = Pet.objects.get_or_create(
            owner=owner, name=data['pet_name'],
            defaults={
                'species': data['species'],
                'birth_date': data['birth_date'],
                'gender': data['gender'],
                'weight': data['weight'],
            },
        )
        return Appointment.objects.create(
            pet=pet,
            doctor=data['doctor'],
            appointment_date=data['appointment_date'],
            appointment_time=data['appointment_time'],
            complaints=data['complaints'] or None,
        )
    def clean_phone(self):
        digits = re.sub(r'\D', '', self.cleaned_data['phone'])
        if len(digits) == 11 and digits[0] in '78':
            digits = digits[1:]
        if len(digits) != 10:
            raise forms.ValidationError('Введите телефон, например +7 (902) 111-22-33')
        return f'+7 ({digits[:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:]}'

    def clean_birth_date(self):
        birth_date = self.cleaned_data['birth_date']
        if birth_date > date.today():
            raise forms.ValidationError('Дата рождения не может быть в будущем')
        if birth_date.year < date.today().year - 40:
            raise forms.ValidationError('Проверьте дату рождения: питомцу не может быть больше 40 лет')
        return birth_date

    def clean_appointment_date(self):
        appointment_date = self.cleaned_data['appointment_date']
        if appointment_date < date.today():
            raise forms.ValidationError('Выберите сегодняшнюю или будущую дату')
        if appointment_date > date.today() + timedelta(days=365):
            raise forms.ValidationError('Запись возможна не дальше чем на год вперёд')
        return appointment_date

    def clean_appointment_time(self):
        appointment_time = self.cleaned_data['appointment_time']
        if not (time(9, 0) <= appointment_time <= time(21, 0)):
            raise forms.ValidationError('Клиника работает с 9:00 до 21:00')
        return appointment_time

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        day = cleaned.get('appointment_date')
        hour = cleaned.get('appointment_time')
        if day and hour and datetime.combine(day, hour) < datetime.now():
            self.add_error('appointment_time', 'Это время уже прошло, выберите другое')
        elif doctor and day and hour:
            busy = Appointment.objects.filter(
                doctor=doctor, appointment_date=day, appointment_time=hour,
            ).exclude(status='Отменён').exists()
            if busy:
                self.add_error('appointment_time', 'Это время у врача уже занято, выберите другое')
        return cleaned
    
    def clean_full_name(self):
        name = ' '.join(self.cleaned_data['full_name'].split())
        if len(name) < 5:
            raise forms.ValidationError('Введите ФИО полностью')
        return name

    def clean_pet_name(self):
        name = self.cleaned_data['pet_name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Кличка слишком короткая')
        return name

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
        appointment = super().save()
        appointment.status = 'Вызов на дом'
        address = self.cleaned_data['address']
        appointment.complaints = f'Адрес визита: {address}. ' + (appointment.complaints or '')
        appointment.save()
        owner = appointment.pet.owner
        if not owner.address:                # записываем адрес, только если там пусто
            owner.address = address
            owner.save()
        return appointment
    
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['name', 'contact', 'message']
        widgets = {'message': forms.Textarea(attrs={'rows': 4})}

    def clean_name(self):
        name = self.cleaned_data['name'].strip()
        if len(name) < 2:
            raise forms.ValidationError('Введите имя')
        return name

    def clean_message(self):
        message = self.cleaned_data['message'].strip()
        if len(message) < 10:
            raise forms.ValidationError('Сообщение слишком короткое (минимум 10 символов)')
        return message