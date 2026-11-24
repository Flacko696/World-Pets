import logging
from django.contrib.auth.views import LoginView
from django.core.cache import cache
logger = logging.getLogger(__name__)
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from datetime import date
from .forms import AppointmentForm, FeedbackForm, HomeVisitForm
from .models import Doctor, Pet, Service, Vaccination
from functools import wraps
from django.core.exceptions import PermissionDenied

PER_PAGE = 20   # пагинация по 20 записей (ТЗ)
SORTS = {'price_asc': 'price', 'price_desc': '-price', 'name': 'name'}


def doctor_required(view):
    @login_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.groups.filter(name='Врачи').exists():
            return view(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper


def index(request):
    services = Service.objects.order_by('id')[:6]
    doctors = Doctor.objects.all()[:3]
    return render(request, 'index.html', {'services': services, 'doctors': doctors})

def too_many(request, name, limit=10, seconds=600):
    """True, если с одного адреса слишком много отправок формы name."""
    key = f'rate:{name}:{request.META.get("REMOTE_ADDR", "")}'
    cache.add(key, 0, seconds)
    try:
        count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, seconds)
        count = 1
    return count > limit

def services(request):
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '')
    sort = request.GET.get('sort', 'price_asc')

    items = Service.objects.order_by(SORTS.get(sort, 'price'))
    if category:
        items = items.filter(category=category)
    if q:
        # SQLite не ищет без учёта регистра для русских букв,
        # поэтому фильтруем в Python
        items = [s for s in items if q.lower() in s.name.lower()]

    page_obj = Paginator(items, PER_PAGE).get_page(request.GET.get('page'))

    # ссылки пагинации должны помнить поиск и фильтры
    params = request.GET.copy()
    params.pop('page', None)

    return render(request, 'services.html', {
        'page_obj': page_obj,
        'categories': Service.objects.values_list('category', flat=True).distinct().order_by('category'),
        'q': q,
        'category': category,
        'sort': sort,
        'querystring': params.urlencode(),
    })


def service_detail(request, pk):
    service = get_object_or_404(Service, pk=pk)
    related = Service.objects.filter(category=service.category).exclude(pk=pk)[:3]
    return render(request, 'service_detail.html', {'service': service, 'related': related})


def doctors(request):
    return render(request, 'doctors.html', {'doctors': Doctor.objects.all()})


def appointment(request):
    if request.method == 'POST':
        if too_many(request, 'appointment'):
            messages.error(request, 'Слишком много заявок с вашего адреса. Попробуйте позже.')
            return redirect('appointment')
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Заявка отправлена! Мы позвоним вам в течение 15 минут.')
            return redirect('appointment')
    else:
        initial = {}
        service_id = request.GET.get('service', '')
        doctor_id = request.GET.get('doctor', '')
        if service_id.isdigit():
            service = Service.objects.filter(pk=service_id).first()
            if service:
                initial['complaints'] = f'Услуга: {service.name}. '
        if doctor_id.isdigit():
            initial['doctor'] = int(doctor_id)
        form = AppointmentForm(initial=initial)
    return render(request, 'appointment.html', {'form': form})


def contacts(request):

    return render(request, 'contacts.html')




def search(request):
    q = request.GET.get('q', '').strip()
    found_services = []
    found_doctors = []
    if q:
        low = q.lower()
        found_services = [
            s for s in Service.objects.all()
            if low in s.name.lower() or low in (s.description or '').lower()
        ]
        found_doctors = [
            d for d in Doctor.objects.all()
            if low in d.full_name.lower() or low in d.specialization.lower()
        ]
    return render(request, 'search.html', {
        'q': q, 'found_services': found_services, 'found_doctors': found_doctors,
    })


@doctor_required   # без входа пустит на /login/, без группы «Врачи» даст 403
def patients(request):
    q = request.GET.get('q', '').strip()
    pets = Pet.objects.select_related('owner', 'species').order_by('name')
    if q:
        low = q.lower()
        pets = [p for p in pets if low in p.name.lower() or low in p.owner.full_name.lower()]

    page_obj = Paginator(pets, PER_PAGE).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'patients.html', {
        'page_obj': page_obj, 'q': q, 'querystring': params.urlencode(),
    })


@doctor_required
def patient_card(request, pk):
    pet = get_object_or_404(Pet.objects.select_related('owner', 'species'), pk=pk)
    vaccinations = list(pet.vaccinations.select_related('doctor').order_by('-vaccination_date'))
    current = {v.pk for v in latest_vaccinations(pet.vaccinations.all())}
    for v in vaccinations:
        v.show_overdue = v.is_overdue and v.pk in current
    overdue_count = sum(1 for v in vaccinations if v.show_overdue)
    appointments = (
        pet.appointments.select_related('doctor')
        .prefetch_related('diagnoses__prescriptions')
        .order_by('-appointment_date', '-appointment_time')
    )
    return render(request, 'patient_card.html', {
        'pet': pet, 'vaccinations': vaccinations,
        'appointments': appointments, 'overdue_count': overdue_count,
    })

def latest_vaccinations(queryset):
    """По каждой паре (питомец, название прививки) оставляет самую свежую запись."""
    latest = {}
    for v in queryset.order_by('vaccination_date', 'pk'):
        latest[(v.pet_id, v.vaccine_name.lower())] = v
    return list(latest.values())


@doctor_required
def reminders(request):
    vaccinations = Vaccination.objects.select_related('pet__owner', 'pet__species')
    overdue = [v for v in latest_vaccinations(vaccinations) if v.is_overdue]
    overdue.sort(key=lambda v: v.expiration_date)
    page_obj = Paginator(overdue, PER_PAGE).get_page(request.GET.get('page'))
    return render(request, 'reminders.html', {'page_obj': page_obj, 'querystring': ''})

def home_visit(request):
    if request.method == 'POST':
        form = HomeVisitForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Вызов оформлен! Мы позвоним вам для подтверждения.')
            return redirect('home_visit')
    else:
        form = HomeVisitForm()
    return render(request, 'home_visit.html', {'form': form})

def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Спасибо! Ваше обращение отправлено администратору.')
            return redirect('feedback')
    else:
        form = FeedbackForm()
    return render(request, 'feedback.html', {'form': form})

class LimitedLoginView(LoginView):
    template_name = 'login.html'
    MAX_ATTEMPTS = 5
    LOCK_SECONDS = 300

    def _key(self, request):
        ip = request.META.get('REMOTE_ADDR', '')
        username = request.POST.get('username', '').lower()
        return f'login_fail:{ip}:{username}'

    def post(self, request, *args, **kwargs):
        if cache.get(self._key(request), 0) >= self.MAX_ATTEMPTS:
            form = self.get_form_class()(request)
            context = self.get_context_data(
                form=form,
                lock_message='Слишком много попыток входа. Попробуйте через 5 минут.',
            )
            return self.render_to_response(context, status=429)
        return super().post(request, *args, **kwargs)

    def form_invalid(self, form):
        key = self._key(self.request)
        cache.set(key, cache.get(key, 0) + 1, self.LOCK_SECONDS)
        logger.warning('Неудачная попытка входа: %s', self.request.POST.get('username', ''))
        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(self._key(self.request))
        return super().form_valid(form)
