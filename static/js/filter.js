/**
 * Высокопроизводительный курсорный Spotlight в стиле Refero / Linear
 * Микрофизика, магнитные кнопки и тактильный отклик (Copy Toast)
 */
document.addEventListener('DOMContentLoaded', () => {
  // 1. Курсорный Spotlight на карточках
  const cards = document.querySelectorAll('.project-card, .tech-card');
  cards.forEach((card) => {
    let rect = null;
    const updateRect = () => { rect = card.getBoundingClientRect(); };

    card.addEventListener('mouseenter', updateRect, { passive: true });
    card.addEventListener('mousemove', (e) => {
      if (!rect) updateRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
    }, { passive: true });

    card.addEventListener('mouseleave', () => {
      rect = null;
      card.style.setProperty('--mouse-x', `-300px`);
      card.style.setProperty('--mouse-y', `-300px`);
    }, { passive: true });
  });

  // 2. Blueprint Grid интерактивный луч на фоне
  const bgGrid = document.querySelector('.bg-blueprint-grid');
  if (bgGrid) {
    let gridRaf = null;
    window.addEventListener('mousemove', (e) => {
      if (gridRaf) cancelAnimationFrame(gridRaf);
      gridRaf = requestAnimationFrame(() => {
        bgGrid.style.setProperty('--mouse-screen-x', `${e.clientX}px`);
        bgGrid.style.setProperty('--mouse-screen-y', `${e.clientY}px`);
      });
    }, { passive: true });
  }

  // 4. Копирование в буфер в 1 клик с тостом
  const copyButtons = document.querySelectorAll('[data-copy]');
  const toast = document.getElementById('toast-notify');

  copyButtons.forEach((btn) => {
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      const textToCopy = btn.getAttribute('data-copy');
      if (!textToCopy) return;

      try {
        await navigator.clipboard.writeText(textToCopy);
        showToast(`✓ Скопировано: @${textToCopy}`);
      } catch (err) {
        // Fallback
        const ta = document.createElement('textarea');
        ta.value = textToCopy;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast(`✓ Скопировано: @${textToCopy}`);
      }
    });
  });

  let toastTimer = null;
  function showToast(msg) {
    if (!toast) return;
    toast.textContent = msg;
    toast.classList.add('is-active');
    if (toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.classList.remove('is-active');
    }, 2400);
  }
});
