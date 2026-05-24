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
   CONTENT — apply data/content.json
   =========================== */
function applyContent(content) {
  document.querySelectorAll('[data-content-key]').forEach(el => {
    const key = el.dataset.contentKey;
    const lang = el.dataset.contentLang;
    if (!content[key]) return;

    if (lang) {
      // Rich content (innerHTML): about bio, pullquotes, etc.
      if (content[key][lang]) el.innerHTML = content[key][lang];
    } else {
      // Simple text: update data-en/data-es so setLang() handles it
      if (content[key].en) el.dataset.en = content[key].en;
      if (content[key].es) el.dataset.es = content[key].es;
    }
  });
}

/* ===========================
   SERVICES — apply data/services.json
   =========================== */
function applyServices(services) {
  services.forEach(service => {
    const article = document.querySelector(`[data-service-key="${service.key}"]`);
    if (!article) return;

    const label = article.querySelector('.service-label');
    if (label && service.label) {
      label.dataset.en = service.label.en;
      label.dataset.es = service.label.es;
    }

    const title = article.querySelector('.service-title');
    if (title && service.title) {
      title.dataset.en = service.title.en;
      title.dataset.es = service.title.es;
    }

    const shortEn = article.querySelector('.service-short.lang-en');
    if (shortEn && service.short) shortEn.innerHTML = service.short.en;
    const shortEs = article.querySelector('.service-short.lang-es');
    if (shortEs && service.short) shortEs.innerHTML = service.short.es;

    const drawerInner = article.querySelector('.service-drawer-inner');
    if (drawerInner && service.detail) {
      const detailEn = drawerInner.querySelector('.lang-en');
      if (detailEn) detailEn.innerHTML = service.detail.en;
      const detailEs = drawerInner.querySelector('.lang-es');
      if (detailEs) detailEs.innerHTML = service.detail.es;
    }
  });
}

/* ===========================
   TESTIMONIALS — render data/testimonials.json
   =========================== */
function renderTestimonials(testimonials) {
  const enTrack = document.querySelector('.testimonials-carousel.lang-en .testimonials-track');
  const esTrack = document.querySelector('.testimonials-carousel.lang-es .testimonials-track');
  if (!enTrack || !esTrack) return;

  function makeCard(quote, name, hidden) {
    const article = document.createElement('article');
    article.className = 'testimonial-card';
    if (hidden) article.setAttribute('aria-hidden', 'true');
    article.innerHTML = `
      <span class="testimonial-quote-mark" aria-hidden="true">"</span>
      <p class="testimonial-text">${quote}</p>
      <p class="testimonial-name">${name}</p>
    `;
    return article;
  }

  const enItems = testimonials.filter(t => t.quote.en);
  const esItems = testimonials.filter(t => t.quote.es);

  enTrack.innerHTML = '';
  esTrack.innerHTML = '';

  // Real cards then duplicates for seamless infinite scroll
  [...enItems, ...enItems].forEach((t, i) =>
    enTrack.appendChild(makeCard(t.quote.en, t.name, i >= enItems.length))
  );
  [...esItems, ...esItems].forEach((t, i) =>
    esTrack.appendChild(makeCard(t.quote.es, t.name, i >= esItems.length))
  );
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
   EVENTS LOADER
   =========================== */
function formatDate(dateStr) {
  const d = new Date(dateStr + 'T00:00:00');
  const day = d.getDate();
  const month = d.toLocaleString('default', { month: 'short' }).toUpperCase();
  return { day, month };
}

function renderEvents(events) {
  const container = document.getElementById('events-list');
  const emptyEl = document.getElementById('events-empty');
  if (!container) return;

  const now = new Date();
  now.setHours(0, 0, 0, 0);

  const upcoming = events.filter(e => {
    if (!e.date) return false;
    return new Date(e.date + 'T00:00:00') >= now;
  }).sort((a, b) => new Date(a.date) - new Date(b.date));

  if (upcoming.length === 0) {
    const section = document.getElementById('events');
    if (section) section.style.display = 'none';
    return;
  }

  if (emptyEl) emptyEl.style.display = 'none';

  container.innerHTML = '';
  upcoming.forEach(event => {
    const { day, month } = formatDate(event.date);

    // Support bilingual title/description (object) or legacy plain string
    const titleEn  = typeof event.title === 'object' ? (event.title.en  || '') : (event.title || '');
    const titleEs  = typeof event.title === 'object' ? (event.title.es  || titleEn) : (event.title || '');
    const descEn   = typeof event.description === 'object' ? (event.description.en  || '') : (event.description || '');
    const descEs   = typeof event.description === 'object' ? (event.description.es  || descEn) : (event.description || '');
    const linkTextEn = event.link_text ? (typeof event.link_text === 'object' ? (event.link_text.en || 'Find out more →') : event.link_text) : 'Find out more →';
    const linkTextEs = event.link_text ? (typeof event.link_text === 'object' ? (event.link_text.es || 'Más información →') : event.link_text) : 'Más información →';

    const locationHtml = event.location
      ? `<p class="event-location">
           <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
           ${event.location}
         </p>`
      : '';
    const linkHtml = event.link
      ? `<a href="${event.link}" target="_blank" rel="noopener noreferrer" class="event-link">
           <span class="lang-en">${linkTextEn}</span><span class="lang-es">${linkTextEs}</span>
         </a>`
      : '';

    const card = document.createElement('article');
    card.className = 'event-card';
    card.innerHTML = `
      <div class="event-date-badge" aria-label="${event.date}">
        <span class="event-date-day">${day}</span>
        <span class="event-date-month">${month}</span>
      </div>
      <div class="event-body">
        <h3><span class="lang-en" data-en="${titleEn}" data-es="${titleEs}">${titleEn}</span></h3>
        ${descEn || descEs ? `<p class="lang-en">${descEn}</p><p class="lang-es">${descEs}</p>` : ''}
        ${locationHtml}
        ${linkHtml}
      </div>
    `;
    container.appendChild(card);
  });

  // Apply current language to newly rendered cards
  setLang(document.body.dataset.lang || 'en');
}

function initEvents() {
  fetch('events/events.json', { cache: 'no-store' })
    .then(r => {
      if (!r.ok) throw new Error('Could not load events');
      return r.json();
    })
    .then(renderEvents)
    .catch(() => {
      const section = document.getElementById('events');
      if (section) section.style.display = 'none';
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

  // Load all JSON content then apply language
  const fetchJSON = url => fetch(url, { cache: 'no-store' }).then(r => r.json());

  Promise.all([
    fetchJSON('data/content.json').catch(() => ({})),
    fetchJSON('data/services.json').catch(() => []),
    fetchJSON('data/testimonials.json').catch(() => []),
  ]).then(([content, services, testimonials]) => {
    applyContent(content);
    applyServices(services);
    renderTestimonials(testimonials);
    initLang();
  });

  initEvents();
});
