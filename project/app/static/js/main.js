// ===== Клиентская валидация формы записи (занятие 9, задание 2) =====
const appointmentForm = document.getElementById('appointment-form');
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

// Возвращает текст ошибки или пустую строку, если всё хорошо
function checkField(field) {
  const value = field.value.trim();

  if (field.required && value === '') return 'Заполните это поле';
  if (value === '') return '';

  if (field.name === 'phone') {
    const digits = value.replace(/\D/g, '');
    const ok = digits.length === 10 || (digits.length === 11 && (digits[0] === '7' || digits[0] === '8'));
    if (!ok) return 'Введите телефон, например +7 (902) 111-22-33';
  }
  if (field.name === 'email' && !EMAIL_RE.test(value)) return 'Введите корректную почту';
  if (field.name === 'full_name' && value.length < 5) return 'Введите ФИО полностью';
  if (field.name === 'pet_name' && value.length < 2) return 'Кличка слишком короткая';
  if (field.name === 'weight' && (Number(value) < 0.1 || Number(value) > 200)) return 'Вес от 0.1 до 200 кг';
  if (field.name === 'complaints' && value.length > 500) return 'Не больше 500 символов';
  return '';
}

function showError(field, message) {
  const box = document.getElementById('error-' + field.name);
  if (box) box.textContent = message;
  field.closest('.field').classList.toggle('field--error', message !== '');
}

if (appointmentForm) {
  const fields = appointmentForm.querySelectorAll('input:not([type="hidden"]), select, textarea');

  appointmentForm.addEventListener('submit', function (event) {
    let valid = true;
    fields.forEach(function (field) {
      const message = checkField(field);
      showError(field, message);
      if (message !== '') valid = false;
    });
    if (!valid) event.preventDefault();   // не отправляем, пока есть ошибки
  });

  // пока пользователь исправляет поле, ошибка обновляется сразу
  fields.forEach(function (field) {
    field.addEventListener('input', function () {
      showError(field, checkField(field));
    });
  });
}

// ===== Избранное и живой фильтр каталога (занятие 9, задание 3) =====
function getFavs() {
  try {
    return JSON.parse(localStorage.getItem('favServices')) || [];
  } catch (e) {
    return [];
  }
}

function saveFavs(list) {
  try {
    localStorage.setItem('favServices', JSON.stringify(list));
  } catch (e) {
    // хранилище недоступно, ничего страшного
  }
}

const searchInput = document.getElementById('live-search');
const favOnlyBtn = document.getElementById('fav-only');
const noResults = document.getElementById('no-results');
const serviceCards = document.querySelectorAll('.service-card');
const favCount = document.getElementById('fav-count');

// Показываем или прячем карточки по тексту и по кнопке «Только избранное»
function applyFilters() {
  if (serviceCards.length === 0) return;
  const text = searchInput.value.trim().toLowerCase();
  const onlyFav = favOnlyBtn.getAttribute('aria-pressed') === 'true';
  const favs = getFavs();
  let shown = 0;

  serviceCards.forEach(function (card) {
    const visible = card.dataset.name.includes(text) && (!onlyFav || favs.includes(card.dataset.id));
    card.hidden = !visible;
    if (visible) shown++;
  });
  noResults.hidden = shown !== 0;
}

// Обновляем сердечки и счётчик в шапке
function updateFavs() {
  const favs = getFavs();
  if (favCount) favCount.textContent = favs.length;
  document.querySelectorAll('.fav').forEach(function (btn) {
    const isOn = favs.includes(btn.dataset.id);
    btn.setAttribute('aria-pressed', String(isOn));
    btn.textContent = isOn ? '♥' : '♡';
  });
}

document.querySelectorAll('.fav').forEach(function (btn) {
  btn.addEventListener('click', function () {
    let favs = getFavs();
    if (favs.includes(btn.dataset.id)) {
      favs = favs.filter(function (id) { return id !== btn.dataset.id; });
    } else {
      favs.push(btn.dataset.id);
    }
    saveFavs(favs);
    updateFavs();
    applyFilters();
  });
});

if (searchInput) searchInput.addEventListener('input', applyFilters);

if (favOnlyBtn) {
  favOnlyBtn.addEventListener('click', function () {
    const pressed = favOnlyBtn.getAttribute('aria-pressed') === 'true';
    favOnlyBtn.setAttribute('aria-pressed', String(!pressed));
    applyFilters();
  });
}

updateFavs();

const burger = document.querySelector('.burger');
const menu = document.getElementById('menu');

if (burger && menu) {
  burger.addEventListener('click', function () {
    const isOpen = menu.classList.toggle('is-open');
    burger.setAttribute('aria-expanded', String(isOpen));
  });
}