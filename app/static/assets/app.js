// Minimal front-end JS (kept intentionally small).
// Future upgrades:
// - add analytics events for Apply/Contact clicks
// - add a lightweight toast system
// - smooth scroll to sections
(function () {
  // noop for now
})();


// Simple dropdown menu (Account)
(function () {
  function closeAll() {
    document.querySelectorAll('[data-menu] .menu').forEach((m) => {
      m.setAttribute('aria-hidden', 'true');
    });
    document.querySelectorAll('[data-menu] .menu-btn').forEach((b) => {
      b.setAttribute('aria-expanded', 'false');
    });
  }

  document.addEventListener('click', (e) => {
    const wrap = e.target.closest('[data-menu]');
    if (!wrap) {
      closeAll();
      return;
    }
    const btn = e.target.closest('.menu-btn');
    if (!btn) return;

    const menu = wrap.querySelector('.menu');
    const isOpen = menu.getAttribute('aria-hidden') === 'false';
    closeAll();
    menu.setAttribute('aria-hidden', isOpen ? 'true' : 'false');
    btn.setAttribute('aria-expanded', isOpen ? 'false' : 'true');
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeAll();
  });

  // initialize
  closeAll();
})();
