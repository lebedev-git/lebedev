/**
 * Серая коробка: комната и мебель из примитивов.
 *
 * Ассетов здесь нет намеренно. Каждый объект помечен именем anchor.*,
 * по которому его потом найдёт и заменит настоящая модель.
 */
import * as THREE from 'three';

import { ROOM, PROJECT_GRID, slotPositions } from './zones.js';

const MAT = {
  floor:   new THREE.MeshLambertMaterial({ color: 0x9c968e }),
  wall:    new THREE.MeshLambertMaterial({ color: 0xb8b4ae }),
  accent:  new THREE.MeshLambertMaterial({ color: 0x6f7a72 }),
  prop:    new THREE.MeshLambertMaterial({ color: 0x8a857e }),
  glass:   new THREE.MeshLambertMaterial({ color: 0xd8e2e6 }),
  rug:     new THREE.MeshLambertMaterial({ color: 0xa8a29a }),
  frame:   new THREE.MeshLambertMaterial({ color: 0xcfcac2 }),
  frameHi: new THREE.MeshLambertMaterial({ color: 0xf0ece4 }),
  frameOff:new THREE.MeshLambertMaterial({ color: 0x8f8a83 }),
};

function box(w, h, d, mat, x, y, z, name) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
  m.position.set(x, y, z);
  if (name) m.name = name;
  return m;
}

/** Строит комнату и мебель. Возвращает группу. */
export function buildRoom() {
  const g = new THREE.Group();
  g.name = 'room';

  const halfW = ROOM.w / 2;
  const halfD = ROOM.d / 2;
  const T = 0.12; // толщина стен

  g.add(box(ROOM.w, T, ROOM.d, MAT.floor, 0, -T / 2, 0, 'anchor.floor'));
  g.add(box(ROOM.w, T, ROOM.d, MAT.wall, 0, ROOM.h + T / 2, 0, 'anchor.ceiling'));
  // Задняя стена — акцентная, на ней висят проекты.
  g.add(box(ROOM.w, ROOM.h, T, MAT.accent, 0, ROOM.h / 2, -halfD - T / 2, 'anchor.wall.back'));
  g.add(box(T, ROOM.h, ROOM.d, MAT.wall, -halfW - T / 2, ROOM.h / 2, 0, 'anchor.wall.left'));
  g.add(box(T, ROOM.h, ROOM.d, MAT.wall, halfW + T / 2, ROOM.h / 2, 0, 'anchor.wall.right'));

  // Ковёр
  g.add(box(2.9, 0.02, 2.0, MAT.rug, 0.3, 0.01, -0.35, 'anchor.rug'));

  // Книжная полка — блог
  g.add(box(2.0, 2.4, 0.45, MAT.prop, -2.15, 1.2, -1.95, 'anchor.blog'));

  // Витрина — достижения
  g.add(box(0.95, 2.2, 0.45, MAT.prop, 2.45, 1.1, -1.95, 'anchor.awards'));
  g.add(box(0.80, 1.9, 0.06, MAT.glass, 2.45, 1.15, -1.70));

  // Стол — контакты
  g.add(box(2.4, 0.06, 0.85, MAT.prop, 0.30, 0.74, -1.75, 'anchor.contact'));
  for (const dx of [-1.12, 1.12]) {
    g.add(box(0.08, 0.74, 0.75, MAT.prop, 0.30 + dx, 0.37, -1.75));
  }
  // Мониторы — чтобы читалась высота стены под рамками
  g.add(box(1.30, 0.42, 0.04, MAT.prop, 0.30, 1.02, -2.05));

  // Кресло
  g.add(box(0.55, 0.10, 0.55, MAT.prop, 0.30, 0.46, -1.05));
  g.add(box(0.55, 0.55, 0.09, MAT.prop, 0.30, 0.78, -0.82));
  g.add(box(0.10, 0.42, 0.10, MAT.prop, 0.30, 0.22, -1.05));

  // Окно на правой стене
  g.add(box(0.04, 1.30, 1.60, MAT.glass, halfW - 0.02, 1.55, -0.30, 'anchor.about'));

  return g;
}

/**
 * Создаёт 12 рамок-слотов. Заполненные становятся кликабельными,
 * пустые остаются глухими — видно, что стена конечна.
 *
 * @param {Array} projects список проектов из DOM (может быть короче SLOT_COUNT)
 * @returns {{group: THREE.Group, pickables: THREE.Mesh[]}}
 */
export function buildProjectWall(projects) {
  const group = new THREE.Group();
  group.name = 'anchor.projects';
  const pickables = [];
  const slots = slotPositions();

  slots.forEach((slot) => {
    const project = projects[slot.index] || null;
    const mat = project
      ? (project.featured ? MAT.frameHi : MAT.frame)
      : MAT.frameOff;

    const mesh = box(
      PROJECT_GRID.frameW, PROJECT_GRID.frameH, 0.035,
      mat, slot.x, slot.y, slot.z,
      `slot.project.${String(slot.index + 1).padStart(2, '0')}`,
    );
    mesh.userData = { slot, project };
    group.add(mesh);
    if (project) pickables.push(mesh);
  });

  return { group, pickables };
}

export function buildLights() {
  const g = new THREE.Group();
  g.add(new THREE.AmbientLight(0xffffff, 1.5));

  const key = new THREE.DirectionalLight(0xffffff, 1.6);
  key.position.set(4, 6, 6);
  g.add(key);

  const fill = new THREE.DirectionalLight(0xdfe6ea, 0.7);
  fill.position.set(-5, 3, 2);
  g.add(fill);

  return g;
}
