/**
 * Движение сайта. Ни одной библиотеки: три наблюдателя и обработчик прокрутки.
 *
 * Анимируются только transform и opacity. При prefers-reduced-motion всё
 * движение выключено на уровне CSS — этот файл просто расставляет классы.
 */

// ── Заголовок по словам ──────────────────────────────────────────────────────
// Разбор происходит после загрузки: в разметке лежит обычный текст, поэтому
// он копируется, читается поисковиком и виден без JS.
document.querySelectorAll('.words').forEach((el) => {
  const words = el.textContent.trim().split(/\s+/);
  el.replaceChildren(...words.flatMap((w, i) => {
    const span = document.createElement('span');
    span.textContent = w;
    span.style.setProperty('--i', i);
    return [span, document.createTextNode(' ')];
  }));
});

// ── Появление при входе в экран ──────────────────────────────────────────────
const reveal = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (!e.isIntersecting) return;
    e.target.classList.add('is-visible');
    reveal.unobserve(e.target);
  });
}, { threshold: 0.18, rootMargin: '0px 0px -8% 0px' });

document.querySelectorAll('.rise, .words').forEach((el) => {
  // Лесенка внутри группы: соседи приходят не разом. Потолок в шесть шагов,
  // иначе последний элемент длинного списка ждёт почти секунду.
  const idx = [...el.parentElement.children].indexOf(el);
  el.style.setProperty('--rise-delay', `${Math.min(idx, 6) * 70}ms`);
  reveal.observe(el);
});

// Страховка: если наблюдатель не отработал — печать, снимок всей страницы,
// нестандартный браузер — контент всё равно проявляется. Невидимое навсегда
// портфолио хуже, чем портфолио без анимации.
setTimeout(() => {
  document.querySelectorAll('.rise:not(.is-visible), .words:not(.is-visible)')
    .forEach((el) => el.classList.add('is-visible'));
}, 2500);

// ── Шапка ────────────────────────────────────────────────────────────────────
const nav = document.querySelector('nav.top');
if (nav) {
  const onScroll = () => nav.classList.toggle('is-compact', scrollY > 24);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  // Шапка меняет тему под полосой, над которой висит: иначе кремовые ссылки
  // оказываются на кремовом фоне и исчезают.
  const bands = document.querySelectorAll('.band-light');
  if (bands.length) {
    const line = new IntersectionObserver((entries) => {
      entries.forEach((e) => nav.classList.toggle('on-light', e.isIntersecting));
    }, { rootMargin: `0px 0px -${Math.max(innerHeight - nav.offsetHeight, 0)}px 0px` });
    bands.forEach((b) => line.observe(b));
  }

  // Меню на узком экране.
  const btn = nav.querySelector('.menu-btn');
  const links = nav.querySelector('.links');
  if (btn && links) {
    btn.addEventListener('click', () => {
      const open = links.classList.toggle('is-open');
      btn.setAttribute('aria-expanded', String(open));
    });
    links.addEventListener('click', (e) => {
      if (e.target.tagName === 'A') links.classList.remove('is-open');
    });
  }
}

// ── Фильтр проектов ──────────────────────────────────────────────────────────
// Раздел проекта — его первый тег, как и в базе.
const filters = document.querySelectorAll('.filter');
if (filters.length) {
  const rows = [...document.querySelectorAll('[data-tags]')];
  filters.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tag = btn.dataset.tag;
      filters.forEach((b) => b.classList.toggle('active', b === btn));
      rows.forEach((row) => {
        const first = (row.dataset.tags || '').split(',')[0].trim();
        row.hidden = tag !== 'all' && first !== tag;
      });
    });
  });
}

// ── Превью обложки за курсором ───────────────────────────────────────────────
// Позиция пишется в переменные, а сдвиг делает CSS: так браузер держит
// анимацию на компоновочном слое и не пересчитывает раскладку на каждое
// движение мыши.
const indexList = document.querySelector('.index');
if (indexList && matchMedia('(hover: hover) and (pointer: fine)').matches) {
  indexList.addEventListener('pointermove', (e) => {
    const row = e.target.closest('a');
    const thumb = row && row.querySelector('.thumb');
    if (!thumb) return;
    const w = thumb.offsetWidth || 240;
    const h = thumb.offsetHeight || 150;
    // Держим превью в кадре: у правого края оно уезжает влево от курсора.
    const x = Math.min(e.clientX + 24, innerWidth - w - 16);
    const y = Math.min(Math.max(e.clientY - h / 2, 16), innerHeight - h - 16);
    thumb.style.setProperty('--px', Math.round(x));
    thumb.style.setProperty('--py', Math.round(y));
  });
}

// ── Видео-обложка ────────────────────────────────────────────────────────────
// Мышь: играет под курсором, после ухода отматывается на первый кадр — иначе
// карточка застывает на случайном кадре из середины ролика.
// Тач: наведения нет, поэтому ролик играет, пока карточка на экране.
{
  const videos = [...document.querySelectorAll('.project-card video')];
  const canHover = matchMedia('(hover: hover) and (pointer: fine)').matches;
  const play = (v) => v.play().catch(() => {});

  if (canHover) {
    videos.forEach((v) => {
      const card = v.closest('.project-card');
      card.addEventListener('pointerenter', () => play(v));
      card.addEventListener('pointerleave', () => { v.pause(); v.currentTime = 0; });
    });
  } else if (videos.length) {
    const seen = new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) play(e.target);
        else { e.target.pause(); e.target.currentTime = 0; }
      });
    }, { threshold: 0.5 });
    videos.forEach((v) => seen.observe(v));
  }
}
