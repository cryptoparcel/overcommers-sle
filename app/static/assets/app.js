/* ─── Overcomers SLE — Main JavaScript ─── */

document.addEventListener("DOMContentLoaded", function () {

  /* ══ Scroll-based topbar shadow ══ */
  var tb = document.getElementById("topbar");
  if (tb) {
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (!ticking) {
        requestAnimationFrame(function () {
          tb.classList.toggle("scrolled", window.scrollY > 8);
          ticking = false;
        });
        ticking = true;
      }
    });
  }

  /* ══ Fade-up on scroll (IntersectionObserver) ══ */
  var fadeEls = document.querySelectorAll(".fade-up");
  if (fadeEls.length > 0 && "IntersectionObserver" in window) {
    var fadeOb = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("visible");
          fadeOb.unobserve(e.target);
        }
      });
    }, { threshold: 0.08, rootMargin: "0px 0px -30px 0px" });
    fadeEls.forEach(function (el) { fadeOb.observe(el); });
  }

  /* ══ Mobile nav toggle ══ */
  var mToggle = document.querySelector(".mobile-toggle");
  var navEl = document.querySelector(".nav");
  if (mToggle && navEl) {
    mToggle.addEventListener("click", function () {
      navEl.classList.toggle("nav--open");
      mToggle.setAttribute("aria-expanded", navEl.classList.contains("nav--open"));
    });
  }

  /* ══ Account dropdown ══ */
  var acctBtn = document.querySelector("[data-toggle='account-menu']");
  var acctMenu = document.getElementById("account-menu");
  if (acctBtn && acctMenu) {
    acctBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      acctMenu.classList.toggle("open");
    });
    document.addEventListener("click", function (e) {
      if (!e.target.closest("#account-menu") && !e.target.closest("[data-toggle='account-menu']")) {
        acctMenu.classList.remove("open");
      }
    });
  }

  /* ═══════════════════════════════
     NOTIFICATION SYSTEM
     ═══════════════════════════════ */
  var notifWrap = document.getElementById("notifWrap");
  var notifBtn = document.getElementById("notifBtn");
  var notifPanel = document.getElementById("notifPanel");
  var notifOverlay = document.getElementById("notifOverlay");
  var notifDot = document.getElementById("notifDot");
  var notifBody = document.getElementById("notifBody");
  var notifClear = document.getElementById("notifClear");
  var notifOpen = false;

  function toggleNotif() {
    notifOpen = !notifOpen;
    if (notifPanel) notifPanel.classList.toggle("open", notifOpen);
    if (notifOverlay) notifOverlay.classList.toggle("open", notifOpen);
    if (notifOpen) {
      setTimeout(function () {
        document.querySelectorAll(".notif-item:not(.read)").forEach(function (item) {
          item.classList.add("read");
        });
        updateNotifDot();
      }, 2000);
    }
  }

  function closeNotif() {
    notifOpen = false;
    if (notifPanel) notifPanel.classList.remove("open");
    if (notifOverlay) notifOverlay.classList.remove("open");
  }

  function markNotifRead(el) {
    el.classList.add("read");
    var link = el.querySelector(".notif-item__action");
    if (link) window.location.href = link.href;
    updateNotifDot();
  }

  function updateNotifDot() {
    var unread = document.querySelectorAll(".notif-item:not(.read)").length;
    if (notifDot) notifDot.classList.toggle("active", unread > 0);
    if (notifClear && notifBody && notifBody.querySelector(".notif-empty")) {
      notifClear.style.display = "none";
    }
  }

  function clearAllNotifs() {
    if (notifBody) {
      notifBody.innerHTML = '<div class="notif-empty"><div class="notif-empty__icon"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--muted);opacity:.5"><polyline points="20 6 9 17 4 12"/></svg></div><div class="notif-empty__text">You\'re all caught up.</div></div>';
    }
    if (notifDot) notifDot.classList.remove("active");
    if (notifClear) notifClear.style.display = "none";
  }

  if (notifBtn) notifBtn.addEventListener("click", toggleNotif);
  if (notifOverlay) notifOverlay.addEventListener("click", closeNotif);
  if (notifClear) notifClear.addEventListener("click", clearAllNotifs);
  document.querySelectorAll(".notif-item").forEach(function (item) {
    item.addEventListener("click", function () { markNotifRead(item); });
  });
  document.addEventListener("click", function (e) {
    if (notifOpen && notifWrap && !e.target.closest("#notifWrap")) closeNotif();
  });

  /* ═══════════════════════════════
     CRISIS RESOURCES TOGGLE
     ═══════════════════════════════ */
  var crisisToggle = document.getElementById("crisisToggle");
  var crisisBody = document.getElementById("crisisBody");
  if (crisisToggle && crisisBody) {
    crisisToggle.addEventListener("click", function () {
      var expanded = crisisToggle.getAttribute("aria-expanded") === "true";
      crisisToggle.setAttribute("aria-expanded", !expanded);
      crisisBody.classList.toggle("open");
    });
  }

  /* ═══════════════════════════════
     PHOTO LIGHTBOX
     ═══════════════════════════════ */
  var lb = document.getElementById("lightbox");
  var lbStage = document.getElementById("lbStage");
  var lbCounter = document.getElementById("lbCurrent");
  var slides = document.querySelectorAll(".lb__slide");
  var thumbs = document.querySelectorAll(".lb__thumb");
  var lbIndex = 0;
  var totalSlides = slides.length;

  window.openLightbox = function (idx) {
    if (!lb || totalSlides === 0) return;
    lbIndex = idx;
    lb.classList.add("open");
    document.body.style.overflow = "hidden";
    showSlide();
  };

  window.closeLightbox = function () {
    if (!lb) return;
    lb.classList.remove("open");
    document.body.style.overflow = "";
  };

  window.navLightbox = function (dir) {
    lbIndex = (lbIndex + dir + totalSlides) % totalSlides;
    showSlide();
  };

  window.goToSlide = function (i) {
    lbIndex = i;
    showSlide();
  };

  function showSlide() {
    slides.forEach(function (s, i) { s.classList.toggle("active", i === lbIndex); });
    thumbs.forEach(function (t, i) { t.classList.toggle("active", i === lbIndex); });
    if (lbCounter) lbCounter.textContent = lbIndex + 1;
    if (thumbs[lbIndex]) thumbs[lbIndex].scrollIntoView({ behavior: "smooth", inline: "center", block: "nearest" });
  }

  document.addEventListener("keydown", function (e) {
    if (lb && lb.classList.contains("open")) {
      if (e.key === "Escape") window.closeLightbox();
      if (e.key === "ArrowLeft") window.navLightbox(-1);
      if (e.key === "ArrowRight") window.navLightbox(1);
    }
    if (e.key === "Escape" && notifOpen) closeNotif();
  });

  if (lbStage) {
    lbStage.addEventListener("click", function (e) {
      if (e.target === lbStage) window.closeLightbox();
    });
  }

  // Touch swipe
  if (lb) {
    var sx = 0, dx = 0;
    lb.addEventListener("touchstart", function (e) { sx = e.touches[0].clientX; dx = 0; }, { passive: true });
    lb.addEventListener("touchmove", function (e) { dx = e.touches[0].clientX - sx; }, { passive: true });
    lb.addEventListener("touchend", function () {
      if (Math.abs(dx) > 50) { if (dx < 0) window.navLightbox(1); else window.navLightbox(-1); }
    });
  }

  /* ══ reCAPTCHA v3 ══ */
  var recapEl = document.getElementById("recaptcha_token");
  if (recapEl && typeof grecaptcha !== "undefined") {
    var siteKey = document.querySelector("meta[name='recaptcha-site-key']");
    if (siteKey) {
      grecaptcha.ready(function () {
        grecaptcha.execute(siteKey.content, { action: "form" }).then(function (token) {
          recapEl.value = token;
        });
      });
    }
  }

  /* ══ Analytics ══ */
  document.querySelectorAll("[data-track]").forEach(function (el) {
    el.addEventListener("click", function () {
      var action = el.getAttribute("data-track");
      if (typeof gtag === "function") gtag("event", action, { event_category: "engagement" });
    });
  });

});

/* ── Password visibility toggle ─────────────────────────── */
function togglePw(id, btn) {
  var inp = document.getElementById(id);
  if (!inp) return;
  var show = inp.type === 'password';
  inp.type = show ? 'text' : 'password';
  btn.classList.toggle('active', show);
  btn.setAttribute('aria-label', show ? 'Hide password' : 'Show password');
}
