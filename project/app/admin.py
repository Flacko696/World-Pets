from django.contrib import admin
from .models import (
    Owner, AnimalSpecies, Pet, Doctor, Service,
    Appointment, Diagnosis, Prescription,
    VaccineSchedule, Vaccination
)

admin.site.register(Owner)
admin.site.register(AnimalSpecies)
admin.site.register(Pet)
admin.site.register(Doctor)
admin.site.register(Service)         
admin.site.register(Appointment)
admin.site.register(Diagnosis)
admin.site.register(Prescription)
admin.site.register(VaccineSchedule)
admin.site.register(Vaccination)