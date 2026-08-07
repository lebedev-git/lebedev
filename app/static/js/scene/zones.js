/**
 * Контракт сцены: размеры комнаты, сетка слотов, точки камеры.
 *
 * Здесь и только здесь живут координаты. Ни main.js, ни room.js не хранят
 * ни одного числа о том, где что стоит. Когда серые коробки заменит настоящая
 * модель, правится этот файл (или значения приезжают из именованных пустышек
 * .glb) — остальной код не трогается.
 */

export const ROOM = {
  w: 6.4,   // ширина  (x: -3.2 .. 3.2)
  h: 3.0,   // высота  (y: 0 .. 3.0)
  d: 4.4,   // глубина (z: -2.2 .. 2.2), передняя стена срезана
};

/** Сетка рамок на задней стене. 12 слотов — жёсткий потолок. */
export const PROJECT_GRID = {
  cols: 4,
  rows: 3,
  frameW: 0.60,
  frameH: 0.42,
  gap: 0.13,
  centerX: 0.30,
  centerY: 2.05,
  z: -2.16,          // чуть перед задней стеной
};

export const SLOT_COUNT = PROJECT_GRID.cols * PROJECT_GRID.rows;

/**
 * Позиции слотов, слева направо и сверху вниз.
 * Порядок важен: избранные проекты попадают в верхний ряд.
 */
export function slotPositions() {
  const g = PROJECT_GRID;
  const gridW = g.cols * g.frameW + (g.cols - 1) * g.gap;
  const gridH = g.rows * g.frameH + (g.rows - 1) * g.gap;
  const x0 = g.centerX - gridW / 2 + g.frameW / 2;
  const y0 = g.centerY + gridH / 2 - g.frameH / 2;

  const out = [];
  for (let r = 0; r < g.rows; r++) {
    for (let c = 0; c < g.cols; c++) {
      out.push({
        index: out.length,
        x: x0 + c * (g.frameW + g.gap),
        y: y0 - r * (g.frameH + g.gap),
        z: g.z,
      });
    }
  }
  return out;
}

/** Именованные точки камеры: откуда смотрим и куда. */
export const ZONES = {
  overview: {
    label: 'Обзор',
    position: [0.0, 4.6, 8.2],
    target: [0.2, 1.3, -1.2],
  },
  projects: {
    label: 'Проекты',
    position: [PROJECT_GRID.centerX, PROJECT_GRID.centerY, 2.0],
    target: [PROJECT_GRID.centerX, PROJECT_GRID.centerY, PROJECT_GRID.z],
  },
};

/** Точка камеры для конкретной рамки — считается из позиции слота. */
export function slotZone(slot) {
  return {
    position: [slot.x, slot.y, slot.z + 1.15],
    target: [slot.x, slot.y, slot.z],
  };
}

/**
 * Самопроверка контракта. Ловит две реальные ошибки: расползание сетки
 * за пределы стены и рассинхрон SLOT_COUNT с реальной раскладкой.
 * Бросает на старте, а не рисует кривую комнату молча.
 */
export function selfTest() {
  const slots = slotPositions();
  if (slots.length !== SLOT_COUNT) {
    throw new Error(`slotPositions вернул ${slots.length}, ожидалось ${SLOT_COUNT}`);
  }
  const halfW = ROOM.w / 2;
  for (const s of slots) {
    const left = s.x - PROJECT_GRID.frameW / 2;
    const right = s.x + PROJECT_GRID.frameW / 2;
    const bottom = s.y - PROJECT_GRID.frameH / 2;
    const top = s.y + PROJECT_GRID.frameH / 2;
    if (left < -halfW || right > halfW) {
      throw new Error(`слот ${s.index} вышел за стену поx: ${left.toFixed(2)}..${right.toFixed(2)}`);
    }
    if (bottom < 0 || top > ROOM.h) {
      throw new Error(`слот ${s.index} вышел за стену по y: ${bottom.toFixed(2)}..${top.toFixed(2)}`);
    }
  }
  return true;
}
