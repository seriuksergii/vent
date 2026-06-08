/** Замініть на ваш реальний домен перед індексацією в Google Search Console */
const SITE_URL = 'https://vodovitrodym.com.ua';
const ASSET_V = '20260608-6';

if ('scrollRestoration' in history) {
  history.scrollRestoration = 'manual';
}

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {});
  });
}

const pageCache = new Map();
let initAbort = new AbortController();
let sectionObserver = null;
let countersDone = false;

function normalizePath(pathname) {
  if (!pathname || pathname === '/' || /\/index\.html$/i.test(pathname)) return '/';
  return pathname;
}

function isAppPage(pathname) {
  const path = normalizePath(pathname);
  return path === '/' || path === '/catalog.html';
}

function ensureStylesheet(href) {
  const base = href?.split('?')[0];
  if (!base || document.querySelector(`link[rel="stylesheet"][href^="${base}"]`)) return;
  const link = document.createElement('link');
  link.rel = 'stylesheet';
  link.href = href;
  document.head.appendChild(link);
}

async function fetchPage(path) {
  const key = normalizePath(path);
  if (pageCache.has(key)) return pageCache.get(key);

  const response = await fetch(key === '/' ? '/' : key, { credentials: 'same-origin' });
  if (!response.ok) return null;

  const html = await response.text();
  pageCache.set(key, html);
  return html;
}

function warmOppositePage() {
  const other = normalizePath(location.pathname) === '/' ? '/catalog.html' : '/';
  fetchPage(other).catch(() => {});
  if (other === '/catalog.html') {
    ensureStylesheet(`catalog.min.css?v=${ASSET_V}`);
  }
}

function updateMetaFromDoc(doc) {
  document.title = doc.title;

  const description = doc.querySelector('meta[name="description"]');
  if (description) {
    let meta = document.querySelector('meta[name="description"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'description';
      document.head.appendChild(meta);
    }
    meta.content = description.content;
  }

  const canonical = document.getElementById('canonicalUrl');
  const sourceCanonical = doc.getElementById('canonicalUrl');
  if (canonical && sourceCanonical) {
    canonical.href = sourceCanonical.href;
  }
}

function scrollToHash(hash, behavior = 'auto') {
  if (!hash) {
    window.scrollTo({ top: 0, behavior });
    return;
  }
  const target = document.querySelector(hash);
  if (target) {
    target.scrollIntoView({ behavior, block: 'start' });
  } else {
    window.scrollTo({ top: 0, behavior });
  }
}

async function navigateTo(path, hash = '', push = true) {
  const targetPath = normalizePath(path);
  const html = await fetchPage(targetPath);
  if (!html) {
    location.href = targetPath + hash;
    return;
  }

  const doc = new DOMParser().parseFromString(html, 'text/html');
  doc.querySelectorAll('link[rel="stylesheet"][href]').forEach((link) => {
    ensureStylesheet(link.getAttribute('href'));
  });

  updateMetaFromDoc(doc);
  document.body.className = doc.body.className;
  document.body.innerHTML = doc.body.innerHTML;

  if (push) {
    history.pushState({ instantNav: true }, '', targetPath + hash);
  }

  countersDone = false;
  initPage();

  requestAnimationFrame(() => scrollToHash(hash));
}

function initPageScroll() {
  const hash = window.location.hash;
  if (!hash) {
    window.scrollTo(0, 0);
  } else {
    scrollToHash(hash);
  }
}

window.addEventListener('pageshow', (event) => {
  if (
    (event.persisted ||
      performance.getEntriesByType('navigation')[0]?.type === 'back_forward') &&
    !window.location.hash
  ) {
    window.scrollTo(0, 0);
  }
});

function syncHeaderHeightVar(signal) {
  const siteHeader = document.getElementById('siteHeader');
  if (!siteHeader) return;

  const apply = () => {
    const h = Math.ceil(siteHeader.getBoundingClientRect().height);
    if (h > 0) {
      document.documentElement.style.setProperty('--header-real-h', `${h}px`);
    }
  };

  apply();
  window.addEventListener('resize', apply, { passive: true, signal });
  window.addEventListener('orientationchange', apply, { passive: true, signal });
  if (document.fonts?.ready) {
    document.fonts.ready.then(apply).catch(() => {});
  }
}

function initScrollHeader(signal) {
  const siteHeader = document.getElementById('siteHeader');
  if (!siteHeader) return;

  const apply = () => {
    siteHeader.classList.toggle('is-scrolled', window.scrollY > 24);
  };

  window.addEventListener('scroll', apply, { passive: true, signal });
  requestAnimationFrame(apply);
}

function initMobileNav(signal) {
  const burgerBtn = document.getElementById('burgerBtn');
  const navMobile = document.getElementById('navMobile');
  const navClose = document.getElementById('navClose');
  if (!burgerBtn || !navMobile || !navClose) return;

  const openMobileNav = () => {
    navMobile.hidden = false;
    navMobile.classList.add('is-open');
    navMobile.setAttribute('role', 'dialog');
    navMobile.setAttribute('aria-modal', 'true');
    burgerBtn.classList.add('is-open');
    burgerBtn.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
    navClose.focus();
  };

  const closeMobileNav = () => {
    navMobile.classList.remove('is-open');
    navMobile.hidden = true;
    navMobile.removeAttribute('role');
    navMobile.removeAttribute('aria-modal');
    burgerBtn.classList.remove('is-open');
    burgerBtn.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
    burgerBtn.focus();
  };

  burgerBtn.addEventListener(
    'click',
    () => {
      if (navMobile.classList.contains('is-open')) closeMobileNav();
      else openMobileNav();
    },
    { signal },
  );
  navClose.addEventListener('click', closeMobileNav, { signal });
  navMobile.querySelectorAll('.nav-mobile-link').forEach((link) => {
    link.addEventListener('click', closeMobileNav, { signal });
  });
  document.addEventListener(
    'keydown',
    (event) => {
      if (event.key === 'Escape' && navMobile.classList.contains('is-open')) {
        closeMobileNav();
      }
    },
    { signal },
  );
}

const revealSelectors =
  '.manufacturer-feature, .manufacturer-text, .products-header, .direction-label, .product-card, .why-card, .step-card, .trust-item, .faq-item';

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

function initSectionAnimations() {
  const sections = document.querySelectorAll('.section');
  sections.forEach((sec, index) => {
    if (
      !sec.classList.contains('section--from-left') &&
      !sec.classList.contains('section--from-right')
    ) {
      sec.classList.add(index % 2 === 0 ? 'section--from-left' : 'section--from-right');
    }
    sec.querySelectorAll(revealSelectors).forEach((el, i) => {
      el.classList.add(i % 2 === 0 ? 'reveal-from-left' : 'reveal-from-right');
      el.style.transitionDelay = `${0.06 * i + 0.1}s`;
    });
  });
}

function initIntersectionObservers() {
  if (sectionObserver) sectionObserver.disconnect();

  const sections = document.querySelectorAll('.section');
  sectionObserver = new IntersectionObserver(
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

  sections.forEach((sec) => sectionObserver.observe(sec));
}

function initDeferredEnhancements() {
  const run = () => {
    document.querySelectorAll('.product-card, .manufacturer-feature').forEach((card) => {
      card.addEventListener('mouseenter', () => {
        card.style.transition = 'transform 0.2s, border-color 0.2s, box-shadow 0.2s';
        card.style.transform = 'scale(1.02)';
      });
      card.addEventListener('mouseleave', () => {
        card.style.transform = '';
      });
    });
  };

  if ('requestIdleCallback' in window) {
    requestIdleCallback(run, { timeout: 2000 });
  } else {
    setTimeout(run, 1);
  }
}

function initInstantNavigation() {
  document.addEventListener(
    'click',
    async (event) => {
      if (event.defaultPrevented) return;

      const anchor = event.target.closest('a[href]');
      if (!anchor || anchor.target === '_blank' || event.metaKey || event.ctrlKey || event.shiftKey) {
        return;
      }

      let url;
      try {
        url = new URL(anchor.href, location.href);
      } catch {
        return;
      }

      if (url.origin !== location.origin || url.pathname.endsWith('.pdf')) return;

      const targetPath = normalizePath(url.pathname);
      const currentPath = normalizePath(location.pathname);

      if (targetPath === currentPath) {
        if (url.hash) {
          event.preventDefault();
          scrollToHash(url.hash, 'smooth');
          history.pushState({ instantNav: true }, '', targetPath + url.search + url.hash);
        }
        return;
      }

      if (!isAppPage(targetPath)) return;

      event.preventDefault();
      await navigateTo(targetPath, url.hash);
    },
    true,
  );

  window.addEventListener('popstate', () => {
    const path = normalizePath(location.pathname);
    if (!isAppPage(path)) return;
    navigateTo(path, location.hash, false);
  });
}

function initPage() {
  initAbort.abort();
  initAbort = new AbortController();
  const { signal } = initAbort;

  syncHeaderHeightVar(signal);
  initScrollHeader(signal);
  initMobileNav(signal);
  annotateCatalogTableCells();
  initSectionAnimations();
  initIntersectionObservers();
  initDeferredEnhancements();
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

document.addEventListener('click', async (event) => {
  const priceBtn = event.target.closest('.download-price');
  if (priceBtn) {
    event.preventDefault();
    try {
      await downloadFile('price.pdf', 'prays-zhestyani-vyroby-opt-roznica.pdf');
    } catch (_) {
      const link = document.createElement('a');
      link.href = 'price.html';
      link.download = 'prays.html';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
    return;
  }

  const xlsxBtn = event.target.closest('.download-price-xlsx');
  if (!xlsxBtn) return;

  event.preventDefault();
  try {
    await downloadFile('price.xlsx', 'prays-zhestyani-vyroby-opt-roznica.xlsx');
  } catch (_) {
    const link = document.createElement('a');
    link.href = 'price.xlsx';
    link.download = 'prays-zhestyani-vyroby-opt-roznica.xlsx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
});

function buildTableColumnLabels(table) {
  const headerRows = Array.from(table.querySelectorAll('thead tr'));
  if (!headerRows.length) return [];

  const grid = [];
  headerRows.forEach((row, rowIndex) => {
    if (!grid[rowIndex]) grid[rowIndex] = [];
    let colIndex = 0;
    Array.from(row.cells).forEach((cell) => {
      while (grid[rowIndex][colIndex]) colIndex += 1;
      const rowSpan = Number(cell.getAttribute('rowspan') || 1);
      const colSpan = Number(cell.getAttribute('colspan') || 1);
      const text = cell.textContent.trim().replace(/\s+/g, ' ');

      for (let r = 0; r < rowSpan; r += 1) {
        const targetRow = rowIndex + r;
        if (!grid[targetRow]) grid[targetRow] = [];
        for (let c = 0; c < colSpan; c += 1) {
          grid[targetRow][colIndex + c] = text;
        }
      }
      colIndex += colSpan;
    });
  });

  const totalCols = Math.max(...grid.map((row) => row.length));
  const labels = [];

  for (let col = 0; col < totalCols; col += 1) {
    const chain = [];
    for (let row = 0; row < grid.length; row += 1) {
      const value = (grid[row][col] || '').trim();
      if (value && chain[chain.length - 1] !== value) chain.push(value);
    }
    labels.push(chain.join(' · '));
  }

  return labels;
}

function annotateCatalogTableCells() {
  document.querySelectorAll('.catalog-table').forEach((table) => {
    const labels = buildTableColumnLabels(table);
    if (!labels.length) return;

    table.querySelectorAll('tbody tr').forEach((row) => {
      Array.from(row.cells).forEach((cell, idx) => {
        if (labels[idx]) cell.setAttribute('data-label', labels[idx]);
      });
    });
  });
}

(function bootstrap() {
  if (window.__pageCache instanceof Map) {
    window.__pageCache.forEach((html, key) => pageCache.set(key, html));
  }

  const path = normalizePath(location.pathname);
  pageCache.set(path, document.documentElement.outerHTML);

  initInstantNavigation();
  initPage();
  initPageScroll();

  const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 200));
  idle(() => warmOppositePage(), { timeout: 1500 });
})();
