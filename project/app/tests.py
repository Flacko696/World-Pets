from datetime import date, timedelta
from unittest import mock
 
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
 
from .forms import AppointmentForm
from .models import AnimalSpecies, Appointment, Doctor, Owner, Pet, Service
from .utils import percent
 
User = get_user_model()
PASSWORD = 'pass12345'
 
 
class NegativeTests(TestCase):
    """Негативные тесты: система предсказуемо ведёт себя в исключительных ситуациях."""
 
    def setUp(self):
        cache.clear()
        self.species = AnimalSpecies.objects.create(name='Кошка')
        self.doctor = Doctor.objects.create(
            full_name='Смирнов Алексей Викторович', specialization='Врач-терапевт',
            experience_years=8, phone='+7 (902) 555-44-31',
        )
        Service.objects.create(name='Вакцинация кошек', price=1100, category='Прививки')
        group = Group.objects.create(name='Врачи')
        doctor_user = User.objects.create_user('doctor1', password=PASSWORD)
        doctor_user.groups.add(group)
        User.objects.create_user('client1', password=PASSWORD)   # обычный пользователь без группы
 
    def valid_data(self, **extra):
        data = {
            'full_name': 'Козлов Андрей Викторович',
            'phone': '+7 (902) 777-88-99',
            'email': 'andrey@example.com',
            'pet_name': 'Барсик',
            'species': self.species.pk,
            'birth_date': '2022-02-01',
            'gender': 'Самец',
            'weight': '4.5',
            'doctor': self.doctor.pk,
            'appointment_date': (date.today() + timedelta(days=3)).isoformat(),
            'appointment_time': '11:00',
            'complaints': 'Плохо ест второй день',
        }
        data.update(extra)
        return data
 
    # 1. Обращение к несуществующей записи возвращает 404
    def test_missing_records_return_404(self):
        response = self.client.get(reverse('service_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, 'Страница не найдена', status_code=404)
 
        self.client.login(username='doctor1', password=PASSWORD)
        response = self.client.get(reverse('patient_card', args=[99999]))
        self.assertEqual(response.status_code, 404)
 
    # 2. Доступ без прав возвращает 403, гость уходит на страницу входа
    def test_cabinet_forbidden_without_rights(self):
        response = self.client.get(reverse('patients'))
        self.assertRedirects(
            response, f"{reverse('login')}?next={reverse('patients')}",
            fetch_redirect_response=False,
        )
 
        self.client.login(username='client1', password=PASSWORD)
        response = self.client.get(reverse('patients'))
        self.assertEqual(response.status_code, 403)
        self.assertContains(response, 'Доступ запрещён', status_code=403)
 
    # 3. Форма с неверными данными не создаёт запись, показывает сообщение и сохраняет значения
    def test_invalid_form_creates_nothing_and_keeps_values(self):
        data = self.valid_data(phone='12345')
        response = self.client.post(reverse('appointment'), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Введите телефон')
        self.assertContains(response, 'Козлов Андрей Викторович')
        self.assertEqual(Appointment.objects.count(), 0)
        self.assertEqual(Owner.objects.count(), 0)
        self.assertEqual(Pet.objects.count(), 0)
 
    # 4. Ошибка в середине операции: данные не меняются (откат транзакции)
    def test_failure_in_middle_of_save_rolls_back(self):
        form = AppointmentForm(self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)
        with mock.patch.object(Appointment.objects, 'create', side_effect=RuntimeError('сбой')):
            with self.assertRaises(RuntimeError):
                form.save()
        self.assertEqual(Owner.objects.count(), 0)
        self.assertEqual(Pet.objects.count(), 0)
        self.assertEqual(Appointment.objects.count(), 0)
 
    # 5. Расчёт на пустой выборке не падает
    def test_calculation_on_empty_sample_does_not_fail(self):
        self.assertEqual(percent(0, 0), 0)
        self.assertEqual(percent(3, 0), 0)
        self.assertEqual(percent(1, 4), 25.0)
 
        self.client.login(username='doctor1', password=PASSWORD)
        response = self.client.get(reverse('reminders'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Просроченных прививок нет')
