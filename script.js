/* script.js — Inma Piqueras Ramos website */

/* ===========================
   LANGUAGE TOGGLE
   =========================== */
function setLang(lang) {
  document.body.dataset.lang = lang;
  localStorage.setItem('lang', lang);

  document.querySelectorAll('[data-en]').forEach(el => {
    const val = lang === 'es' ? el.dataset.es : el.dataset.en;
    if (val !== undefined) el.innerHTML = val;
  });

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.lang === lang);
    btn.setAttribute('aria-pressed', btn.dataset.lang === lang ? 'true' : 'false');
  });
}

function initLang() {
  const saved = localStorage.getItem('lang');
  const browser = navigator.language ? navigator.language.slice(0, 2).toLowerCase() : 'en';
  const lang = saved || (browser === 'es' ? 'es' : 'en');
  setLang(lang);

  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => setLang(btn.dataset.lang));
  });
}

/* ===========================
   MOBILE NAV
   =========================== */
function initMobileNav() {
  const hamburger = document.getElementById('nav-hamburger');
  const mobileNav = document.getElementById('nav-mobile');
  if (!hamburger || !mobileNav) return;

  hamburger.addEventListener('click', () => {
    const isOpen = mobileNav.classList.toggle('open');
    hamburger.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
    hamburger.textContent = isOpen ? '✕' : '☰';
  });

  mobileNav.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      mobileNav.classList.remove('open');
      hamburger.setAttribute('aria-expanded', 'false');
      hamburger.textContent = '☰';
    });
  });
}

/* ===========================
   SERVICES — expand toggle + photo cycling
   =========================== */
function initServices() {
  const holdMs = parseFloat(
    getComputedStyle(document.documentElement)
      .getPropertyValue('--photo-hold') || '10'
  ) * 1000;

  document.querySelectorAll('.service-section').forEach(section => {
    const btn      = section.querySelector('.service-expand-btn');
    const drawer   = section.querySelector('.service-drawer');
    const photoCol = section.querySelector('.service-photo-col');
    const imgA     = section.querySelector('.service-photo');

    section.addEventListener('click', () => {
      const isExpanded = section.classList.toggle('expanded');
      if (btn)    btn.setAttribute('aria-expanded', String(isExpanded));
      if (drawer) drawer.setAttribute('aria-hidden', String(!isExpanded));
    });

    let images;
    try { images = JSON.parse(section.dataset.images || '[]'); } catch (e) { return; }
    if (images.length < 2 || !imgA || !photoCol) return;

    const imgB = document.createElement('img');
    imgB.className = 'service-photo';
    imgB.style.opacity = '0';
    imgB.alt = '';
    photoCol.appendChild(imgB);

    let idx = 0, aOnTop = true;
    setInterval(() => {
      if (!section.classList.contains('expanded')) return;
      idx = (idx + 1) % images.length;
      if (aOnTop) {
        imgB.src = images[idx];
        imgA.style.opacity = '0';
        imgB.style.opacity = '1';
      } else {
        imgA.src = images[idx];
        imgB.style.opacity = '0';
        imgA.style.opacity = '1';
      }
      aOnTop = !aOnTop;
    }, holdMs);
  });
}

/* ===========================
   SECTION DIVIDER PARALLAX
   =========================== */
function initDividerParallax() {
  const dividers = Array.from(document.querySelectorAll('.section-divider'));
  if (!dividers.length) return;

  const range = parseFloat(
    getComputedStyle(document.documentElement)
      .getPropertyValue('--divider-parallax-range') || '20'
  );

  function update() {
    const vh = window.innerHeight;
    dividers.forEach(divider => {
      const img = divider.querySelector('.divider-img');
      if (!img) return;
      const rect = divider.getBoundingClientRect();
      const centreOffset = (rect.top + rect.height / 2 - vh / 2) / vh;
      img.style.transform = `translateY(${-centreOffset * range}%)`;
    });
    requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

/* ===========================
   HERO TITLE PARALLAX
   =========================== */
function initParallax() {
  const moveEl  = document.querySelector('.hero-title-move');
  const beingEl = document.querySelector('.hero-title-being');
  if (!moveEl || !beingEl) return;

  const style    = getComputedStyle(document.documentElement);
  const strength = parseFloat(style.getPropertyValue('--hero-parallax') || '0.12');
  const lerp     = parseFloat(style.getPropertyValue('--hero-lerp')     || '0.05');

  let current = 0;
  let target  = 0;

  window.addEventListener('scroll', () => {
    target = window.scrollY;
  }, { passive: true });

  function tick() {
    current += (target - current) * lerp;
    const offset = current * strength;
    moveEl.style.transform  = `translateX(${-offset}px)`;
    beingEl.style.transform = `translateX(${offset}px)`;
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ===========================
   ACTIVE NAV SECTION
   =========================== */
function initActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');

  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;
      const id = entry.target.id;
      navLinks.forEach(link => {
        const active = link.getAttribute('href') === `#${id}`;
        link.classList.toggle('active', active);
      });
    });
  }, {
    rootMargin: '-40% 0px -55% 0px',
    threshold: 0
  });

  sections.forEach(s => observer.observe(s));
}

/* ===========================
   FOOTER YEAR
   =========================== */
function initFooterYear() {
  const el = document.getElementById('year');
  if (el) el.textContent = new Date().getFullYear();
}

/* ===========================
   INIT
   =========================== */
document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initServices();
  initFooterYear();
  initParallax();
  initDividerParallax();
  initActiveNav();
  initLang();
});
