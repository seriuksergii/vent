/** Замініть на ваш реальний домен перед індексацією в Google Search Console */
const SITE_URL = 'https://vodovitrodym.com.ua';

if ('scrollRestoration' in history) {
  history.scrollRestoration = 'manual';
}

function initPageScroll() {
  const navType = performance.getEntriesByType('navigation')[0]?.type;
  const hash = window.location.hash;

  // Після F5 браузер часто залишає #ctaSection / #contacts — відкриваємо зверху
  if (navType === 'reload' && hash) {
    history.replaceState(
      null,
      '',
      window.location.pathname + window.location.search,
    );
    window.scrollTo(0, 0);
    return;
  }

  if (!hash) {
    window.scrollTo(0, 0);
  }
}

window.addEventListener('load', initPageScroll);
window.addEventListener('pageshow', (event) => {
  if (
    (event.persisted ||
      performance.getEntriesByType('navigation')[0]?.type === 'back_forward') &&
    !window.location.hash
  ) {
    window.scrollTo(0, 0);
  }
});

(function initCanonical() {
  const canonical = document.getElementById('canonicalUrl');
  if (!canonical) return;
  const path = window.location.pathname.replace(/index\.html$/i, '') || '/';
  const base = SITE_URL.replace(/\/$/, '');
  canonical.href = base + (path === '/' ? '/' : path);
})();

const siteHeader = document.getElementById('siteHeader');
const burgerBtn = document.getElementById('burgerBtn');
const navMobile = document.getElementById('navMobile');
const navClose = document.getElementById('navClose');

if (siteHeader) {
  window.addEventListener(
    'scroll',
    () => {
      siteHeader.classList.toggle('is-scrolled', window.scrollY > 24);
    },
    { passive: true },
  );
  siteHeader.classList.toggle('is-scrolled', window.scrollY > 24);
}

function openMobileNav() {
  navMobile.classList.add('is-open');
  navMobile.setAttribute('aria-hidden', 'false');
  burgerBtn.classList.add('is-open');
  burgerBtn.setAttribute('aria-expanded', 'true');
  document.body.style.overflow = 'hidden';
}

function closeMobileNav() {
  navMobile.classList.remove('is-open');
  navMobile.setAttribute('aria-hidden', 'true');
  burgerBtn.classList.remove('is-open');
  burgerBtn.setAttribute('aria-expanded', 'false');
  document.body.style.overflow = '';
}

if (burgerBtn && navMobile && navClose) {
  burgerBtn.addEventListener('click', () => {
    if (navMobile.classList.contains('is-open')) {
      closeMobileNav();
    } else {
      openMobileNav();
    }
  });
  navClose.addEventListener('click', closeMobileNav);
  document.querySelectorAll('.nav-mobile-link').forEach((link) => {
    link.addEventListener('click', closeMobileNav);
  });
}

const sections = document.querySelectorAll('.section');
const revealSelectors =
  '.manufacturer-feature, .manufacturer-text, .products-header, .direction-label, .product-card, .why-card, .step-card, .trust-item, .faq-item';

sections.forEach((sec, index) => {
  if (
    !sec.classList.contains('section--from-left') &&
    !sec.classList.contains('section--from-right')
  ) {
    sec.classList.add(
      index % 2 === 0 ? 'section--from-left' : 'section--from-right',
    );
  }
  sec.querySelectorAll(revealSelectors).forEach((el, i) => {
    el.classList.add(i % 2 === 0 ? 'reveal-from-left' : 'reveal-from-right');
    el.style.transitionDelay = `${0.06 * i + 0.1}s`;
  });
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        if (entry.target.id === 'trustSection') animateCounters();
      }
    });
  },
  { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
);

sections.forEach((sec) => observer.observe(sec));

let countersDone = false;
function animateCounters() {
  if (countersDone) return;
  countersDone = true;
  document.querySelectorAll('[data-count]').forEach((el) => {
    const target = +el.dataset.count;
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 1400;
    const start = performance.now();
    function tick(now) {
      const p = Math.min((now - start) / duration, 1);
      const ease = 1 - Math.pow(1 - p, 3);
      el.textContent = prefix + Math.round(target * ease) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
}

const trustSection = document.getElementById('trustSection');
if (
  trustSection &&
  trustSection.getBoundingClientRect().top < window.innerHeight
) {
  animateCounters();
}

function triggerFileDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

async function downloadFile(path, name) {
  const res = await fetch(path);
  if (!res.ok) throw new Error('download failed');
  triggerFileDownload(await res.blob(), name);
}

document.querySelectorAll('.download-price').forEach((btn) => {
  btn.addEventListener('click', async () => {
    try {
      await downloadFile('price.pdf', 'prays-zhestyani-vyroby-opt-roznica.pdf');
    } catch (_) {
      // fallback: якщо PDF недоступний, пробуємо HTML
      const link = document.createElement('a');
      link.href = 'price.html';
      link.download = 'prays.html';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  });
});

document.querySelectorAll('.download-price-xlsx').forEach((btn) => {
  btn.addEventListener('click', async () => {
    try {
      await downloadFile('price.xlsx', 'prays-zhestyani-vyroby-opt-roznica.xlsx');
    } catch (_) {
      // fallback: відкриваємо файл як звичайне посилання
      const link = document.createElement('a');
      link.href = 'price.xlsx';
      link.download = 'prays-zhestyani-vyroby-opt-roznica.xlsx';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  });
});

document
  .querySelectorAll('.product-card, .manufacturer-feature')
  .forEach((card) => {
    card.addEventListener('mouseenter', () => {
      card.style.transition =
        'transform 0.2s, border-color 0.2s, box-shadow 0.2s';
      card.style.transform = 'scale(1.02)';
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = '';
    });
  });
