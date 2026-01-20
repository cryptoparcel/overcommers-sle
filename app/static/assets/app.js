(function(){
  // Apply modal
  const openers = document.querySelectorAll('[data-open-apply]');
  const backdrop = document.getElementById('applyModal');
  const closeBtn = document.getElementById('applyClose');

  function open(){
    if(!backdrop) return;
    backdrop.classList.add('open');
    backdrop.setAttribute('aria-hidden','false');
    const first = backdrop.querySelector('input');
    if(first) first.focus();
  }
  function close(){
    if(!backdrop) return;
    backdrop.classList.remove('open');
    backdrop.setAttribute('aria-hidden','true');
  }

  openers.forEach(btn => btn.addEventListener('click', (e) => { e.preventDefault(); open(); }));
  if(closeBtn) closeBtn.addEventListener('click', close);
  if(backdrop){
    backdrop.addEventListener('click', (e) => { if(e.target === backdrop) close(); });
    document.addEventListener('keydown', (e) => { if(e.key === 'Escape') close(); });
  }

  // Active nav (only for in-page anchors)
  const navLinks = Array.from(document.querySelectorAll('.nav a[href^="#"]'));
  const sections = navLinks.map(a => document.querySelector(a.getAttribute('href'))).filter(Boolean);
  if(sections.length){
    const setActive = (id) => {
      navLinks.forEach(a => a.style.background = 'transparent');
      const active = navLinks.find(a => a.getAttribute('href') === '#' + id);
      if(active) active.style.background = 'rgba(14,165,160,.10)';
    };
    const io = new IntersectionObserver((entries) => {
      const visible = entries.filter(e => e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
      if(visible) setActive(visible.target.id);
    }, { threshold: [0.25, 0.5, 0.75]});
    sections.forEach(s => io.observe(s));
  }
})();
