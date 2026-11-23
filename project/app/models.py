from datetime import date

from django.db import models


class Owner(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ФИО")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Телефон")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    address = models.TextField(blank=True, null=True, verbose_name="Адрес (для вызова на дом)")

    class Meta:
        verbose_name = "Владелец"
        verbose_name_plural = "Владельцы"

    def __str__(self):
        return self.full_name


class AnimalSpecies(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название вида")
    care_features = models.TextField(blank=True, null=True, verbose_name="Особенности ухода")

    class Meta:
        verbose_name = "Вид животного"
        verbose_name_plural = "Виды животных"

    def __str__(self):
        return self.name


class Pet(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="pets", verbose_name="Владелец")
    species = models.ForeignKey(AnimalSpecies, on_delete=models.PROTECT, related_name="pets", verbose_name="Вид животного")
    name = models.CharField(max_length=100, verbose_name="Кличка")
    birth_date = models.DateField(verbose_name="Дата рождения")
    gender = models.CharField(max_length=15, verbose_name="Пол", help_text="Самец или Самка")
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Вес, кг")
    breed = models.CharField(max_length=100, blank=True, null=True, verbose_name="Порода")

    class Meta:
        verbose_name = "Питомец"
        verbose_name_plural = "Питомцы"

    def __str__(self):
        return f"{self.name} ({self.species.name})"


class Doctor(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="ФИО")
    specialization = models.CharField(max_length=100, verbose_name="Специализация")
    experience_years = models.PositiveIntegerField(default=1, verbose_name="Стаж, лет")
    phone = models.CharField(max_length=20, unique=True, verbose_name="Телефон")
    photo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Фото (путь к файлу)")

    class Meta:
        verbose_name = "Врач"
        verbose_name_plural = "Врачи"

    @property
    def initials(self):
        # "Смирнов Алексей Викторович" -> "СА"
        parts = self.full_name.split()
        return ''.join(p[0] for p in parts[:2]).upper()

    def __str__(self):
        return f"Др. {self.full_name} ({self.specialization})"


class Service(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название услуги")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена (руб.)")
    category = models.CharField(max_length=100, default="Общие услуги", verbose_name="Категория")

    class Meta:
        verbose_name = "Услуга"
        verbose_name_plural = "Услуги"

    def __str__(self):
        return f"{self.name} — {self.price} руб."


class Appointment(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="appointments", verbose_name="Питомец")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name="appointments", verbose_name="Врач")
    appointment_date = models.DateField(verbose_name="Дата приёма")
    appointment_time = models.TimeField(verbose_name="Время приёма")
    status = models.CharField(max_length=30, default="Запланирован", verbose_name="Статус",
                              help_text="Например: Запланирован, Завершён, Отменён")
    complaints = models.TextField(blank=True, null=True, verbose_name="Жалобы")

    class Meta:
        verbose_name = "Приём"
        verbose_name_plural = "Приёмы"

    def __str__(self):
        return f"Приём {self.pet.name} ({self.appointment_date})"


class Diagnosis(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="diagnoses", verbose_name="Приём")
    disease_name = models.CharField(max_length=200, verbose_name="Название болезни")
    symptoms_description = models.TextField(blank=True, null=True, verbose_name="Описание симптомов")
    is_cured = models.BooleanField(default=False, verbose_name="Вылечен")

    class Meta:
        verbose_name = "Диагноз"
        verbose_name_plural = "Диагнозы"

    def __str__(self):
        return self.disease_name


class Prescription(models.Model):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, related_name="prescriptions", verbose_name="Диагноз")
    medication_or_procedure = models.CharField(max_length=200, verbose_name="Лекарство или процедура")
    dosage = models.CharField(max_length=100, verbose_name="Дозировка")
    course_duration = models.CharField(max_length=100, verbose_name="Длительность курса")
    recommendations = models.TextField(blank=True, null=True, verbose_name="Рекомендации")

    class Meta:
        verbose_name = "Назначение"
        verbose_name_plural = "Назначения"

    def __str__(self):
        return f"{self.medication_or_procedure} ({self.dosage})"


class VaccineSchedule(models.Model):
    species = models.ForeignKey(AnimalSpecies, on_delete=models.CASCADE, related_name="schedules", verbose_name="Вид животного")
    recommended_age_months = models.PositiveIntegerField(verbose_name="Рекомендуемый возраст, мес.")
    vaccine_name = models.CharField(max_length=150, verbose_name="Название прививки")
    repeat_period_months = models.PositiveIntegerField(default=12, verbose_name="Повтор через, мес.")

    class Meta:
        verbose_name = "Запись графика прививок"
        verbose_name_plural = "График прививок"

    def __str__(self):
        return f"{self.vaccine_name} ({self.species.name})"


class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="vaccinations", verbose_name="Питомец")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name="vaccinations", verbose_name="Врач")
    vaccine_name = models.CharField(max_length=150, verbose_name="Название прививки")
    vaccination_date = models.DateField(verbose_name="Дата прививки")
    expiration_date = models.DateField(verbose_name="Действует до")
    batch_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер партии")

    class Meta:
        verbose_name = "Прививка"
        verbose_name_plural = "Прививки"

    @property
    def is_overdue(self):
        return date.today() > self.expiration_date

    def __str__(self):
        return f"{self.vaccine_name} для {self.pet.name}"

class Feedback(models.Model):
    name = models.CharField(max_length=100, verbose_name="Имя")
    contact = models.CharField(max_length=100, verbose_name="Телефон или email")
    message = models.TextField(max_length=1000, verbose_name="Сообщение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Отправлено")
    is_processed = models.BooleanField(default=False, verbose_name="Обработано")

    class Meta:
        verbose_name = "Обращение"
        verbose_name_plural = "Обращения"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.created_at:%d.%m.%Y})"