// hero.js — rotating-word hero animation and nav toggle.
// Vanilla JS, no dependencies.  Respects prefers-reduced-motion.

(function () {
  'use strict';

  // --- Rotating hero words --------------------------------------------------

  const rotator = document.querySelector('.hero__rotator');
  if (rotator) {
    const words = Array.from(rotator.querySelectorAll('.hero__word'));
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (words.length && !reduced) {
      let i = 0;
      words.forEach((w, idx) => w.setAttribute('data-active', idx === 0 ? 'true' : 'false'));
      setInterval(() => {
        words[i].setAttribute('data-active', 'false');
        i = (i + 1) % words.length;
        words[i].setAttribute('data-active', 'true');
      }, 2400);
    } else if (words.length && reduced) {
      words[0].setAttribute('data-active', 'true');
    }
  }

  // --- Mobile nav toggle ----------------------------------------------------

  const toggle = document.querySelector('.nav-toggle');
  const nav = document.getElementById('primary-nav');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      const open = nav.getAttribute('data-open') === 'true';
      nav.setAttribute('data-open', open ? 'false' : 'true');
      toggle.setAttribute('aria-expanded', open ? 'false' : 'true');
    });
  }

  // --- Counter rollups (simple one-shot when scrolled into view) ------------

  const counters = document.querySelectorAll('.counter__value[data-count-to]');
  if (counters.length && 'IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.getAttribute('data-count-to'), 10) || 0;
        const duration = 1500;
        const start = performance.now();
        function tick(now) {
          const t = Math.min(1, (now - start) / duration);
          const eased = 1 - Math.pow(1 - t, 3);
          el.textContent = Math.round(eased * target);
          if (t < 1) requestAnimationFrame(tick);
          else el.textContent = target;
        }
        requestAnimationFrame(tick);
        obs.unobserve(el);
      });
    }, { threshold: 0.5 });
    counters.forEach((c) => obs.observe(c));
  }
})();
