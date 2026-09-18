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
    const smoke = ['~  ', ' ~ ', '  ~'];
    const w = cols();
    const el = line('', 'tg');
    el.style.whiteSpace = 'pre';
    const frame = (pad, i) => {
      const puff = smoke[i % 3];
      const rows = [' '.repeat(6) + puff, ...train];
      return rows.map((r) => (pad >= 0 ? ' '.repeat(pad) + r : r.slice(-pad))).join('\n');
    };
    if (REDUCED) { el.textContent = frame(Math.floor(w / 3), 0); return; }
    for (let pad = w, i = 0; pad > -train[1].length; pad -= 2, i++) {
      el.textContent = frame(pad, i);
      await sleep(55);
    }
    drop(el);
    line('поезд ушёл. рутина осталась на перроне.', 'dim');
  },

  async matrix() {
    const w = cols(), rows = 7;
    const chars = 'ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄ0123456789ABCDEF';
    const rnd = () => Array.from({ length: w }, () => (Math.random() < 0.35 ? chars[Math.random() * chars.length | 0] : ' ')).join('');
    const el = line('', 'ok');
    el.style.whiteSpace = 'pre';
    const frames = REDUCED ? 1 : 36;
    for (let i = 0; i < frames; i++) {
      el.textContent = Array.from({ length: rows }, rnd).join('\n');
      await sleep(70);
    }
    if (!REDUCED) drop(el);
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

  async rm() {
    const items = ['отчёты руками', 'копипаст из почты в CRM', 'расшифровка созвонов', 'напоминания клиентам'];
    for (const it of items) {
      const el = line('', 'n8n');
      const steps = REDUCED ? 1 : 12;
      for (let i = 1; i <= steps; i++) {
        const done = Math.round((i / steps) * 18);
        el.textContent = `удаляю: ${it.padEnd(26)} ${'█'.repeat(done)}${'░'.repeat(18 - done)} ${Math.round((i / steps) * 100)}%`;
        await sleep(45);
      }
    }
    line('✓ рутина удалена · освобождено 37 ч/нед');
    link('написать в Telegram', TG, '[agent] хочешь так же? → ');
  },

  async sudo() {
    const el = line('[sudo] password for guest: ', 'dim');
    for (let i = 0; i < 8; i++) { el.textContent += '•'; await sleep(REDUCED ? 0 : 60); }
    await sleep(400);
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
