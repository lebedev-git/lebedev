// плавное появление блоков при скролле
const io = new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach((el, i) => {
  el.style.transitionDelay = ((i % 6) * 60) + 'ms';
  io.observe(el);
});

// мобильное меню
const burger = document.querySelector('.burger');
const links = document.querySelector('.nav-links');
if (burger && links) {
  burger.addEventListener('click', () => links.classList.toggle('open'));
}

// фильтр проектов по тегам
const filters = document.querySelectorAll('.filter');
const cards = document.querySelectorAll('.pcard[data-tags]');
if (filters.length) {
  filters.forEach((f) => {
    f.addEventListener('click', () => {
      filters.forEach((x) => x.classList.remove('active'));
      f.classList.add('active');
      const tag = f.dataset.tag;
      cards.forEach((c) => {
        const tags = (c.dataset.tags || '').toLowerCase();
        const show = tag === 'all' || tags.includes(tag.toLowerCase());
        c.style.display = show ? '' : 'none';
      });
    });
  });
}
