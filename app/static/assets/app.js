// Minimal front-end JS
(function () {
  function track(name, extra) {
    try {
      // For now: just log. You can later send this to analytics endpoint.
      console.log("[track]", name, extra || {});
    } catch (e) {}
  }

  document.addEventListener("click", function (e) {
    var el = e.target.closest("[data-track]");
    if (!el) return;
    track(el.getAttribute("data-track"), { href: el.getAttribute("href") || null });
  });
})();

// reCAPTCHA v3 token helper (no-op if not enabled)
(function () {
  function setTokenOnForms() {
    var tokenInputs = document.querySelectorAll('input[name="recaptcha_token"]');
    if (!tokenInputs || tokenInputs.length === 0) return;

    if (typeof grecaptcha === "undefined" || !grecaptcha.execute) {
      // Keys not configured or script blocked; server-side validation will handle it.
      return;
    }

    grecaptcha.ready(function () {
      // Use the current path as an action label
      var action = (window.location.pathname || "/").replace(/\//g, "_").replace(/^_+/, "") || "page";
      grecaptcha.execute(window.RECAPTCHA_SITE_KEY, { action: action }).then(function (token) {
        tokenInputs.forEach(function (inp) {
          inp.value = token;
        });
      });
    });
  }

  document.addEventListener("DOMContentLoaded", setTokenOnForms);
})();

// Simple dropdown menu (Account)
(function () {
  function closeAll() {
    document.querySelectorAll("[data-menu] .menu").forEach((m) => {
      m.setAttribute("aria-hidden", "true");
    });
    document.querySelectorAll("[data-menu] .menu-btn").forEach((b) => {
      b.setAttribute("aria-expanded", "false");
    });
  }

  document.addEventListener("click", (e) => {
    const wrap = e.target.closest("[data-menu]");
    if (!wrap) {
      closeAll();
      return;
    }
    const btn = e.target.closest(".menu-btn");
    if (!btn) return;

    const menu = wrap.querySelector(".menu");
    const isOpen = menu.getAttribute("aria-hidden") === "false";
    closeAll();
    menu.setAttribute("aria-hidden", isOpen ? "true" : "false");
    btn.setAttribute("aria-expanded", isOpen ? "false" : "true");
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeAll();
  });

  closeAll();
})();
