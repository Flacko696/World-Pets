from datetime import date
from django.db import models

class Owner(models.Model):
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True, verbose_name="Адрес (для вызова на дом)")

    def __str__(self):
        return self.full_name

class AnimalSpecies(models.Model):
    name = models.CharField(max_length=100, unique=True)
    care_features = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class Pet(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="pets")
    species = models.ForeignKey(AnimalSpecies, on_delete=models.PROTECT, related_name="pets")
    name = models.CharField(max_length=100)
    birth_date = models.DateField()
    gender = models.CharField(max_length=15)
    weight = models.DecimalField(max_digits=5, decimal_places=2)
    breed = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.species.name})"

class Doctor(models.Model):
    full_name = models.CharField(max_length=150)
    specialization = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField(default=1)
    phone = models.CharField(max_length=20, unique=True)
    photo = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Др. {self.full_name} ({self.specialization})"

class Service(models.Model):
    name = models.CharField(max_length=150, verbose_name="Название услуги")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена (руб.)")
    category = models.CharField(max_length=100, default="Общие услуги", verbose_name="Категория")

    def __str__(self):
        return f"{self.name} — {self.price} руб."

class Appointment(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name="appointments")
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=30, default="Запланирован")
    complaints = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Приём {self.pet.name} ({self.appointment_date})"

class Diagnosis(models.Model):
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="diagnoses")
    disease_name = models.CharField(max_length=200)
    symptoms_description = models.TextField(blank=True, null=True)
    is_cured = models.BooleanField(default=False)

    def __str__(self):
        return self.disease_name

class Prescription(models.Model):
    diagnosis = models.ForeignKey(Diagnosis, on_delete=models.CASCADE, related_name="prescriptions")
    medication_or_procedure = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    course_duration = models.CharField(max_length=100)
    recommendations = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medication_or_procedure} ({self.dosage})"

class VaccineSchedule(models.Model):
    species = models.ForeignKey(AnimalSpecies, on_delete=models.CASCADE, related_name="schedules")
    recommended_age_months = models.PositiveIntegerField()
    vaccine_name = models.CharField(max_length=150)
    repeat_period_months = models.PositiveIntegerField(default=12)

    def __str__(self):
        return f"{self.vaccine_name} ({self.species.name})"

class Vaccination(models.Model):
    pet = models.ForeignKey(Pet, on_delete=models.CASCADE, related_name="vaccinations")
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name="vaccinations")
    vaccine_name = models.CharField(max_length=150)
    vaccination_date = models.DateField()
    expiration_date = models.DateField()
    batch_number = models.CharField(max_length=50, blank=True, null=True)

    @property
    def is_overdue(self):
        return date.today() > self.expiration_date

    def __str__(self):
        return f"{self.vaccine_name} для {self.pet.name}"