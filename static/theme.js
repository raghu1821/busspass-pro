/* ============================================================
   BusPass Pro — Theme Toggle & Mobile Menu Handler
   Handles: dark/light mode, hamburger, preference persistence
   ============================================================ */

(function () {

  // ── Theme Engine ────────────────────────────────────────────
  const STORAGE_KEY = 'buspass-theme';

  function applyTheme(mode) {
    if (mode === 'light') {
      document.body.classList.add('light-mode');
    } else {
      document.body.classList.remove('light-mode');
    }
    updateIcon(mode);
    localStorage.setItem(STORAGE_KEY, mode);
  }

  function updateIcon(mode) {
    const icons = document.querySelectorAll('#themeIcon');
    icons.forEach(el => { el.textContent = mode === 'light' ? '☀️' : '🌙'; });
  }

  function getPreferredTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return saved;
    // Respect OS preference
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  // Apply immediately (before paint) to avoid flash
  const initial = getPreferredTheme();
  applyTheme(initial);

  // Wire toggle button(s) — runs after DOM ready
  document.addEventListener('DOMContentLoaded', function () {
    updateIcon(localStorage.getItem(STORAGE_KEY) || 'dark');

    document.querySelectorAll('#themeToggle').forEach(btn => {
      btn.addEventListener('click', function () {
        const isLight = document.body.classList.contains('light-mode');
        applyTheme(isLight ? 'dark' : 'light');
      });
    });

    // ── Hamburger Menu ─────────────────────────────────────────
    const hamburger = document.getElementById('hamburger');
    const mobileNav = document.getElementById('mobileNav');

    if (hamburger && mobileNav) {
      hamburger.addEventListener('click', function (e) {
        e.stopPropagation();
        const open = mobileNav.classList.toggle('open');
        hamburger.classList.toggle('open', open);
        hamburger.setAttribute('aria-expanded', open);
      });

      // Close when clicking outside
      document.addEventListener('click', function (e) {
        if (!hamburger.contains(e.target) && !mobileNav.contains(e.target)) {
          mobileNav.classList.remove('open');
          hamburger.classList.remove('open');
        }
      });

      // Close on link click
      mobileNav.querySelectorAll('a').forEach(link => {
        link.addEventListener('click', function () {
          mobileNav.classList.remove('open');
          hamburger.classList.remove('open');
        });
      });
    }
  });

})();
