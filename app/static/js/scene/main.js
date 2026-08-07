/**
 * Сцена: сборка, маршрут камеры, наведение и выбор рамки.
 *
 * Контент не грузится отдельным запросом — он уже отрендерен сервером
 * в #projects-data. Тот же самый разметочный слой служит дублем для
 * поисковиков и фолбэком, если WebGL недоступен.
 */
import * as THREE from 'three';

import { ZONES, slotZone, selfTest } from './zones.js';
import { buildRoom, buildProjectWall, buildLights } from './room.js';

selfTest();

// ── Данные из DOM ────────────────────────────────────────────────────────────
function readProjects() {
  return [...document.querySelectorAll('#projects-data article[data-slug]')].map((card) => ({
    slug: card.dataset.slug,
    title: card.dataset.title,
    summary: card.dataset.summary || '',
    tags: (card.dataset.tags || '').split(',').map((t) => t.trim()).filter(Boolean),
    role: card.dataset.role || '',
    year: card.dataset.year || '',
    link: card.dataset.link || '',
    featured: card.dataset.featured === '1',
    body: card.querySelector('.p-body')?.textContent.trim() || '',
  }));
}

// Избранные — в верхний ряд.
const projects = readProjects().sort((a, b) => Number(b.featured) - Number(a.featured));

// ── Рендерер ─────────────────────────────────────────────────────────────────
const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x74706b);

const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);

scene.add(buildLights());
scene.add(buildRoom());

const wall = buildProjectWall(projects);
scene.add(wall.group);

// ── Маршрут камеры ───────────────────────────────────────────────────────────
const cam = {
  pos: new THREE.Vector3(),
  target: new THREE.Vector3(),
  fromPos: new THREE.Vector3(),
  fromTarget: new THREE.Vector3(),
  toPos: new THREE.Vector3(),
  toTarget: new THREE.Vector3(),
  t: 1,
  duration: 0.95,
};

const easeInOutCubic = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);

function flyTo(zone, duration = 0.95) {
  cam.fromPos.copy(cam.pos);
  cam.fromTarget.copy(cam.target);
  cam.toPos.set(...zone.position);
  cam.toTarget.set(...zone.target);
  cam.duration = duration;
  cam.t = 0;
}

function snapTo(zone) {
  cam.pos.set(...zone.position);
  cam.target.set(...zone.target);
  cam.toPos.copy(cam.pos);
  cam.toTarget.copy(cam.target);
  cam.t = 1;
}

snapTo(ZONES.overview);

// ── Состояние навигации ──────────────────────────────────────────────────────
let currentZone = 'overview';
let selected = null;
let hovered = null;

const panel = document.getElementById('panel');
const crumbs = document.getElementById('crumbs');

function goZone(name) {
  currentZone = name;
  selected = null;
  flyTo(ZONES[name]);
  closePanel();
  syncCrumbs();
}

function selectSlot(mesh) {
  selected = mesh;
  currentZone = 'projects';
  flyTo(slotZone(mesh.userData.slot), 0.8);
  openPanel(mesh.userData.project);
  syncCrumbs();
}

function syncCrumbs() {
  const parts = [{ id: 'overview', label: 'Комната' }];
  if (currentZone === 'projects') parts.push({ id: 'projects', label: 'Проекты' });
  if (selected) parts.push({ id: null, label: selected.userData.project.title });

  crumbs.innerHTML = '';
  parts.forEach((p, i) => {
    if (i) crumbs.append(Object.assign(document.createElement('span'), {
      className: 'sep', textContent: '/',
    }));
    if (p.id) {
      const b = document.createElement('button');
      b.textContent = p.label;
      b.onclick = () => goZone(p.id);
      crumbs.append(b);
    } else {
      crumbs.append(Object.assign(document.createElement('span'), {
        className: 'current', textContent: p.label,
      }));
    }
  });
}

// ── Панель контента ──────────────────────────────────────────────────────────
function el(tag, className, text) {
  const n = document.createElement(tag);
  if (className) n.className = className;
  if (text) n.textContent = text;
  return n;
}

/** Тексты приходят из админки — вставляем только как текст, не как разметку. */
function openPanel(p) {
  panel.replaceChildren();

  const close = el('button', 'close', '×');
  close.setAttribute('aria-label', 'Закрыть');
  close.onclick = () => goZone('projects');
  panel.append(close);

  const meta = [p.role, p.year].filter(Boolean).join(' · ');
  if (meta) panel.append(el('div', 'meta', meta));
  panel.append(el('h2', null, p.title));
  if (p.summary) panel.append(el('p', 'summary', p.summary));

  if (p.tags.length) {
    const tags = el('div', 'tags');
    p.tags.forEach((t) => tags.append(el('span', null, t)));
    panel.append(tags);
  }
  if (p.body) panel.append(el('div', 'body', p.body));

  const actions = el('div', 'actions');
  const page = el('a', 'primary', 'Открыть страницу');
  page.href = `/projects/${encodeURIComponent(p.slug)}`;
  actions.append(page);

  if (/^https?:\/\//i.test(p.link)) {
    const ext = el('a', null, 'Ссылка');
    ext.href = p.link;
    ext.target = '_blank';
    ext.rel = 'noopener';
    actions.append(ext);
  }
  panel.append(actions);
  panel.classList.add('open');
}

function closePanel() {
  panel.classList.remove('open');
}

// ── Наведение и клик ─────────────────────────────────────────────────────────
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let pointerInside = false;

canvas.addEventListener('pointermove', (e) => {
  const r = canvas.getBoundingClientRect();
  pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1;
  pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1;
  pointerInside = true;
});
canvas.addEventListener('pointerleave', () => { pointerInside = false; });

canvas.addEventListener('click', () => {
  if (hovered) selectSlot(hovered);
  else if (selected) goZone('projects');
  else if (currentZone === 'overview') goZone('projects');
});

addEventListener('keydown', (e) => {
  if (e.key !== 'Escape') return;
  if (selected) goZone('projects');
  else if (currentZone !== 'overview') goZone('overview');
});

document.getElementById('btn-overview').onclick = () => goZone('overview');
document.getElementById('btn-projects').onclick = () => goZone('projects');

function updateHover() {
  // Во время полёта не подсвечиваем — иначе рамки «прыгают» под курсором.
  const active = pointerInside && cam.t >= 1 && !selected;
  const hit = active
    ? raycaster.intersectObjects(wall.pickables, false)[0]?.object || null
    : null;

  if (hit === hovered) return;
  if (hovered) hovered.scale.set(1, 1, 1);
  hovered = hit;
  if (hovered) hovered.scale.set(1.08, 1.08, 2.5);
  canvas.style.cursor = hovered ? 'pointer' : 'default';
}

// ── Цикл ─────────────────────────────────────────────────────────────────────
function resize() {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  // Ноль бывает, когда канвас в скрытой вкладке: aspect стал бы NaN.
  if (!w || !h) return;
  if (canvas.width === w && canvas.height === h) return;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}

const clock = new THREE.Clock();

function tick() {
  const dt = clock.getDelta();

  if (cam.t < 1) {
    cam.t = Math.min(1, cam.t + dt / cam.duration);
    const k = easeInOutCubic(cam.t);
    cam.pos.lerpVectors(cam.fromPos, cam.toPos, k);
    cam.target.lerpVectors(cam.fromTarget, cam.toTarget, k);
  }
  camera.position.copy(cam.pos);
  camera.lookAt(cam.target);

  resize();
  raycaster.setFromCamera(pointer, camera);
  updateHover();
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}

syncCrumbs();
document.body.classList.add('scene-ready');
tick();
