from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from app import views
from app.views import LimitedLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('services/', views.services, name='services'),
    path('services/<int:pk>/', views.service_detail, name='service_detail'),
    path('doctors/', views.doctors, name='doctors'),
    path('appointment/', views.appointment, name='appointment'),
    path('contacts/', views.contacts, name='contacts'),
    path('search/', views.search, name='search'),
    path('login/', LimitedLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('doctor/patients/', views.patients, name='patients'),
    path('doctor/patients/<int:pk>/', views.patient_card, name='patient_card'),
    path('doctor/reminders/', views.reminders, name='reminders'),
    path('home-visit/', views.home_visit, name='home_visit'),
    path('feedback/', views.feedback, name='feedback'),
]