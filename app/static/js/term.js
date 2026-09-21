/**
 * Терминал в hero: пасхалки по командам.
 *
 * Стартует пустым с подсказкой, отвечает на команды. Всё — textContent
 * и несколько кадров анимации; при prefers-reduced-motion показывается только
 * финальный кадр.
 */
const term = document.getElementById('term-body');
const form = document.getElementById('term-form');
const input = document.getElementById('term-input');
if (!term || !form || !input) throw new Error('term: нет разметки');

const TG = term.dataset.tg || '#';
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

let busy = false;

// ── Вывод ────────────────────────────────────────────────────────────────────
function kind(s) {
  const m = s.match(/^\[(\w+)\]/);
  if (m) return m[1];
  if (s.startsWith('$')) return 'cmd';
  if (s.startsWith('✓')) return 'ok';
  return '';
}

function line(text = '', k = kind(text)) {
  const el = document.createElement('span');
  el.className = 'ln';
  if (k) el.dataset.k = k;
  el.textContent = text;
  term.append(el, '\n');
  term.scrollTop = term.scrollHeight;
  return el;
}

/** Убрать строку вместе с её переводом строки. */
function drop(el) {
  if (el.nextSibling && el.nextSibling.nodeType === 3) el.nextSibling.remove();
  el.remove();
}

function link(text, href, prefix = '') {
  const el = line(prefix, '');
  const a = document.createElement('a');
  a.href = href; a.textContent = text;
  if (href.startsWith('http')) { a.target = '_blank'; a.rel = 'noopener'; }
  el.append(a);
  return el;
}

/** Ширина терминала в символах — нужна кадровым анимациям. */
function cols() {
  const probe = document.createElement('span');
  probe.textContent = 'M'.repeat(20);
  probe.style.visibility = 'hidden';
  term.append(probe);
  const w = probe.getBoundingClientRect().width / 20;
  probe.remove();
  return Math.max(24, Math.floor((term.clientWidth - 32) / w));
}

const MENU = [['matrix', 'дождь'], ['sl', 'поезд'], ['coffee', 'перерыв'],
  ['rm -rf routine', 'удалить рутину'], ['sudo hire', 'нанять'], ['ls', 'проекты'], ['clear', 'очистить']];

/** Меню команд; первая строка выделена, её же подставляем в ввод. */
function menu() {
  MENU.forEach(([c, d]) => { line(`${c.padEnd(16)} ${d}`, 'dim').dataset.cmd = c; });
  pick = 0;
  input.value = MENU[0][0];
  highlightRow();
}

// ── Эффекты за пределами окна ────────────────────────────────────────────────
// Терминал управляет страницей: слой поверх всего, сам себя убирает.
function overlay(tag = 'div', cls = '') {
  const el = document.createElement(tag);
  el.className = `term-fx ${cls}`.trim();
  document.body.append(el);
  return el;
}

/** Дождь из символов на весь экран — за содержимым страницы, ничего не перекрывает. */
async function rainScreen(ms = 3200) {
  const cv = overlay('canvas', 'term-fx-rain');
  const ctx = cv.getContext('2d');
  const dpr = devicePixelRatio || 1;
  cv.width = innerWidth * dpr; cv.height = innerHeight * dpr;
  ctx.scale(dpr, dpr);
  const size = 16, chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ0123456789';
  const drops = Array.from({ length: Math.ceil(innerWidth / size) }, () => Math.random() * -40);
  ctx.font = `${size}px ${getComputedStyle(term).fontFamily}`;
  const t0 = performance.now();
  await new Promise((done) => {
    const tick = (now) => {
      // Хвосты гаснут в прозрачность, а не в чёрный: фон страницы остаётся виден.
      ctx.globalCompositeOperation = 'destination-out';
      ctx.fillStyle = 'rgba(0, 0, 0, 0.14)';
      ctx.fillRect(0, 0, innerWidth, innerHeight);
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = '#59D6C0';
      drops.forEach((y, i) => {
        ctx.fillText(chars[Math.random() * chars.length | 0], i * size, y * size);
        drops[i] = y * size > innerHeight && Math.random() > 0.97 ? 0 : y + 0.6;
      });
      if (now - t0 < ms) requestAnimationFrame(tick); else done();
    };
    requestAnimationFrame(tick);
  });
  await cv.animate({ opacity: 0 }, { duration: 700, fill: 'forwards' }).finished;
  cv.remove();
}

/** Поезд проезжает по низу экрана справа налево. */
async function trainScreen(rows) {
  const el = overlay('pre', 'term-fx-train');
  el.textContent = rows.join('\n');
  const w = el.getBoundingClientRect().width;
  await el.animate(
    [{ transform: `translateX(${innerWidth}px)` }, { transform: `translateX(${-w - 40}px)` }],
    { duration: Math.max(2800, innerWidth * 2.4), easing: 'linear' },
  ).finished;
  el.remove();
}

/** Слово «рутину» в подзаголовке: обернуть, чтобы зачеркнуть и стереть. */
function routineWord() {
  const lead = document.querySelector('.hero-copy .lead');
  const old = lead && lead.querySelector('.erased');
  if (old) return old;
  const node = lead && [...lead.childNodes].find((n) => n.nodeType === 3 && n.data.includes('рутину'));
  if (!node) return null;
  const mid = node.splitText(node.data.indexOf('рутину'));
  mid.splitText(6);
  const span = document.createElement('span');
  span.className = 'erased';
  span.textContent = mid.data;
  mid.replaceWith(span);
  return span;
}

/** Всё на странице падает вниз, через паузу возвращается на места. */
async function collapseScreen() {
  const els = [...document.querySelectorAll(
    '.hero-title, .hero-copy .lead, .tech-card, .project-card, .skill-card, .sec-title, .biz-card',
  )];
  const anims = els.map((el) => el.animate(
    [{ transform: 'none' }, { transform: `translate(${(Math.random() - 0.5) * 200}px, 110vh) rotate(${(Math.random() - 0.5) * 60}deg)` }],
    { duration: 900 + Math.random() * 500, delay: Math.random() * 600, easing: 'cubic-bezier(.55, 0, 1, .45)', fill: 'forwards' },
  ));
  await Promise.all(anims.map((a) => a.finished));
  await sleep(1400);
  anims.forEach((a) => { a.reverse(); });
  await Promise.all(anims.map((a) => a.finished));
  anims.forEach((a) => a.cancel());
}

// ── Команды ──────────────────────────────────────────────────────────────────
const CMDS = {
  async sl() {
    const train = [
      '        ____      ',
      '   ____|[]|______ ',
      '  |  __  __  __  |',
      '  |_/  \\/  \\/  \\_|',
      '     o  o  o  o   ',
    ];
    if (REDUCED) {
      const el = line('', 'tg');
      el.style.whiteSpace = 'pre';
      el.textContent = train.join('\n');
    } else {
      line('чух-чух… смотри вниз.', 'tg');
      await trainScreen(['      ~  ~', ...train]);
    }
    line('поезд ушёл. рутина осталась на перроне.', 'dim');
  },

  async matrix() {
    const w = cols(), rows = 7;
    const chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ0123456789ABCDEF';
    const rnd = () => Array.from({ length: w }, () => (Math.random() < 0.35 ? chars[Math.random() * chars.length | 0] : ' ')).join('');
    const el = line('', 'ok');
    el.style.whiteSpace = 'pre';
    if (REDUCED) {
      el.textContent = Array.from({ length: rows }, rnd).join('\n');
    } else {
      // дождь начинается в окне и через полсекунды выходит на весь экран
      const inWindow = (async () => { for (let i = 0; i < 8; i++) { el.textContent = Array.from({ length: rows }, rnd).join('\n'); await sleep(70); } })();
      await Promise.all([inWindow, rainScreen()]);
      drop(el);
    }
    line('wake up. ты уже в матрице.', 'ok');
  },

  async coffee() {
    const cup = (s) => [
      `      ${s}`,
      '    ........',
      '    |      |]',
      '    \\      /',
      '     `----\'',
    ].join('\n');
    const steam = ['( (', ' ) )', '( ('];
    const el = line('', 'claude');
    el.style.whiteSpace = 'pre';
    const n = REDUCED ? 1 : 8;
    for (let i = 0; i < n; i++) { el.textContent = cup(steam[i % 3]); await sleep(320); }
    line('перерыв 5 минут. агенты работают без тебя.', 'dim');
  },

  async rm(cmd) {
    if (/\s\/$/.test(cmd)) {
      line('rm: cannot remove \'/\': permission denied', 'n8n');
      line('попробуй sudo.', 'dim');
      return;
    }
    const items = ['отчёты руками', 'копипаст из почты в CRM', 'расшифровка созвонов', 'напоминания клиентам'];
    const word = REDUCED ? null : routineWord();   // слово в подзаголовке зачёркивается вместе с прогрессом
    word?.classList.remove('gone');
    for (const [n, it] of items.entries()) {
      const el = line('', 'n8n');
      const steps = REDUCED ? 1 : 12;
      for (let i = 1; i <= steps; i++) {
        const done = Math.round((i / steps) * 18);
        el.textContent = `удаляю: ${it.padEnd(26)} ${'█'.repeat(done)}${'░'.repeat(18 - done)} ${Math.round((i / steps) * 100)}%`;
        word?.style.setProperty('--w', (n + i / steps) / items.length);
        await sleep(45);
      }
    }
    word?.classList.add('gone');
    line('✓ рутина удалена · освобождено 37 ч/нед');
    link('написать в Telegram', TG, '[agent] хочешь так же? → ');
    line('а если совсем всё? sudo rm -rf /', 'dim');
    if (word) setTimeout(() => { word.classList.remove('gone'); word.style.removeProperty('--w'); }, 6000);
  },

  async sudo(cmd) {
    const el = line('[sudo] password for guest: ', 'dim');
    for (let i = 0; i < 8; i++) { el.textContent += '•'; await sleep(REDUCED ? 0 : 60); }
    await sleep(400);
    if (/\brm\b/.test(cmd)) {
      line('permission granted. удаляю /…', 'n8n');
      if (!REDUCED) await collapseScreen();
      line('✓ восстановлено из бэкапа. бэкапы — это важно.');
      return;
    }
    line('permission granted.', 'ok');
    link(TG.replace(/^https?:\/\//, ''), TG, '→ ');
  },

  ls() {
    const cards = [...document.querySelectorAll('.project-card')];
    if (!cards.length) { line('пусто', 'dim'); return; }
    cards.forEach((c) => {
      const go = c.querySelector('.project-go');
      if (!go) return;
      const title = c.querySelector('.project-title')?.textContent.trim() || go.href;
      link(title, go.href, '→ ');
    });
  },

  clear() { term.replaceChildren(); menu(); },
};

const ALIAS = { кофе: 'coffee', поезд: 'sl', train: 'sl' };

async function run(raw) {
  const cmd = raw.trim();
  if (!cmd) return;
  line(`$ ${cmd}`, 'cmd');
  const word = ALIAS[cmd.toLowerCase()] || cmd.split(/\s+/)[0].toLowerCase();
  const fn = CMDS[word];
  if (fn) { await fn(cmd); return; }
  line(`command not found: ${word}`, 'n8n');
  const near = Object.keys(CMDS).find((k) => k.startsWith(word[0]));
  line(near ? `может, ${near}?` : 'команды — стрелками ↑/↓', 'dim');
}

// ── Ввод ─────────────────────────────────────────────────────────────────────
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  if (busy) return;
  const value = input.value;
  input.value = '';
  setGhost();
  busy = true;
  try { await run(value); } finally { busy = false; }
});

// ── Подсказка и выбор команды ────────────────────────────────────────────────
// Ввёл первые буквы — серым дописывается остаток, Tab или → принимает.
// ↑/↓ листают список команд прямо в строке ввода, Enter запускает.
const COMMANDS = MENU.map(([c]) => c);
const ghost = document.getElementById('term-ghost');
let pick = -1;

function suggestion() {
  const v = input.value.toLowerCase();
  if (!v) return '';
  return COMMANDS.find((c) => c.startsWith(v) && c !== v) || '';
}

function setGhost() {
  const s = suggestion();
  if (!ghost) return;
  ghost.textContent = '';
  if (!s) return;
  const typed = document.createElement('span');
  typed.className = 'typed';
  typed.textContent = input.value;
  ghost.append(typed, s.slice(input.value.length));
}

function highlightRow() {
  term.querySelectorAll('.ln[data-cmd]').forEach((el) => {
    el.classList.toggle('is-pick', el.dataset.cmd === input.value);
  });
}

input.addEventListener('input', () => { setGhost(); highlightRow(); });

input.addEventListener('keydown', (e) => {
  if (e.key === 'Tab' || (e.key === 'ArrowRight' && input.selectionStart === input.value.length)) {
    const s = suggestion();
    if (s) { e.preventDefault(); input.value = s; setGhost(); }
    else if (e.key === 'Tab') e.preventDefault();
    return;
  }
  if (e.key === 'ArrowUp' || e.key === 'ArrowDown') {
    e.preventDefault();
    const step = e.key === 'ArrowDown' ? 1 : -1;
    pick = (pick + step + COMMANDS.length) % COMMANDS.length;
    input.value = COMMANDS[pick];
    setGhost();
    highlightRow();
  }
});

// Клик по терминалу — фокус в строку ввода. Но не когда выделяют текст
// для копирования: смена фокуса сбросила бы выделение.
term.closest('.hero-terminal').addEventListener('click', (e) => {
  if (e.target.closest('a, button')) return;
  if (String(getSelection())) return;
  input.focus({ preventScroll: true });
});

menu();
