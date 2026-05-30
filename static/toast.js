/* ============================================================
   BusPass Pro — Global Toast & AJAX Action Handler
   Provides: showToast(), downloadFile(), ajaxAction()
   ============================================================ */

// ── Toast Engine ──────────────────────────────────────────────
(function () {
  // Inject container once
  function getContainer() {
    let c = document.getElementById('toast-container');
    if (!c) {
      c = document.createElement('div');
      c.id = 'toast-container';
      document.body.appendChild(c);
    }
    return c;
  }

  /**
   * showToast(title, message, type, duration)
   * type: 'success' | 'error' | 'info' | 'warning'
   */
  window.showToast = function (title, message, type = 'success', duration = 4000) {
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
    const container = getContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span class="toast-icon">${icons[type] || '🔔'}</span>
      <div class="toast-body">
        <div class="toast-title">${title}</div>
        ${message ? `<div class="toast-msg">${message}</div>` : ''}
      </div>
      <button class="toast-close" onclick="dismissToast(this.parentElement)">✕</button>
    `;

    container.appendChild(toast);

    // Auto-dismiss
    const timer = setTimeout(() => dismissToast(toast), duration);
    toast._timer = timer;
  };

  window.dismissToast = function (toast) {
    if (!toast || toast.classList.contains('toast-hide')) return;
    clearTimeout(toast._timer);
    toast.classList.add('toast-hide');
    setTimeout(() => toast.remove(), 350);
  };
})();


// ── Download Handler (no page navigation) ────────────────────
/**
 * Call on Download PDF button click.
 * Triggers file download silently and shows toast.
 */
window.downloadFile = function (url, btn) {
  if (btn) {
    btn.classList.add('btn-loading');
    const orig = btn.innerHTML;
    btn.innerHTML = '⏳ Downloading...';
    setTimeout(() => {
      btn.innerHTML = orig;
      btn.classList.remove('btn-loading');
    }, 3000);
  }

  showToast('Downloading…', 'Your PDF pass is being prepared.', 'info', 2500);

  // Create invisible iframe to trigger download without navigation
  const a = document.createElement('a');
  a.href = url;
  a.download = '';
  a.style.display = 'none';
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    a.remove();
    showToast('Download Complete', 'Your PDF bus pass has been downloaded.', 'success');
  }, 2000);
};


// ── AJAX Action Handler ───────────────────────────────────────
/**
 * ajaxAction(url, options)
 * Performs a GET fetch and shows toast. Optionally refreshes page.
 *
 * options = {
 *   btn:         HTMLElement  — button to show loading state on
 *   loadingText: string       — text while loading
 *   successTitle: string
 *   successMsg:   string
 *   errorTitle:   string
 *   reload:       bool        — reload page after success (default false)
 *   reloadDelay:  number ms   — delay before reload (default 1200)
 *   onSuccess:    function()  — callback on success
 * }
 */
window.ajaxAction = function (url, options = {}) {
  const {
    btn,
    loadingText = 'Processing…',
    successTitle = 'Done!',
    successMsg = 'Action completed successfully.',
    errorTitle = 'Error',
    reload = false,
    reloadDelay = 1400,
    onSuccess = null,
  } = options;

  let origHTML = null;
  if (btn) {
    origHTML = btn.innerHTML;
    btn.innerHTML = `⏳ ${loadingText}`;
    btn.classList.add('btn-loading');
    btn.disabled = true;
  }

  fetch(url, { credentials: 'same-origin' })
    .then(res => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.text();
    })
    .then(() => {
      showToast(successTitle, successMsg, 'success');
      if (btn) {
        btn.innerHTML = '✅ Done';
        setTimeout(() => {
          btn.innerHTML = origHTML;
          btn.classList.remove('btn-loading');
          btn.disabled = false;
        }, 1800);
      }
      if (onSuccess) onSuccess();
      if (reload) setTimeout(() => location.reload(), reloadDelay);
    })
    .catch(err => {
      showToast(errorTitle, 'Something went wrong. Please try again.', 'error');
      console.error(err);
      if (btn) {
        btn.innerHTML = origHTML;
        btn.classList.remove('btn-loading');
        btn.disabled = false;
      }
    });
};


// ── Flash message → Toast on page load ───────────────────────
// If Flask flashes a message via URL param ?msg=...&type=success
document.addEventListener('DOMContentLoaded', function () {
  const params = new URLSearchParams(window.location.search);
  const msg  = params.get('msg');
  const type = params.get('type') || 'success';
  if (msg) {
    showToast(
      type === 'error' ? 'Error' : 'Notice',
      decodeURIComponent(msg),
      type
    );
    // Clean URL without reload
    const clean = window.location.pathname;
    window.history.replaceState({}, '', clean);
  }
});
