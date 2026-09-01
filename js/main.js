/**
 * NexusSphere - Interactive Main JavaScript Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  initThemeToggle();
  initMobileMenu();
  initReadingProgressBar();
  initTableOfContents();
  initCategoryFilters();
  initFaqAccordion();
  initInteractiveForms();
  initShareButtons();
});

/* ==========================================
   Theme Management (Light / Dark)
   ========================================== */
function initThemeToggle() {
  const themeToggleButtons = document.querySelectorAll('.theme-toggle-btn');
  const savedTheme = localStorage.getItem('ns_theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  
  applyTheme(savedTheme);

  themeToggleButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
      applyTheme(newTheme);
      showToast(`Switched to ${newTheme} mode`);
    });
  });
}

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('ns_theme', theme);
  
  const themeIcons = document.querySelectorAll('.theme-toggle-icon');
  themeIcons.forEach(icon => {
    icon.textContent = theme === 'dark' ? '☀️' : '🌙';
  });
}

/* ==========================================
   Mobile Navigation Menu
   ========================================== */
function initMobileMenu() {
  const toggleBtn = document.querySelector('.mobile-menu-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggleBtn && navLinks) {
    toggleBtn.addEventListener('click', () => {
      navLinks.classList.toggle('open');
      const isOpen = navLinks.classList.contains('open');
      toggleBtn.setAttribute('aria-expanded', isOpen);
      toggleBtn.innerHTML = isOpen ? '✕' : '☰';
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!toggleBtn.contains(e.target) && !navLinks.contains(e.target) && navLinks.classList.contains('open')) {
        navLinks.classList.remove('open');
        toggleBtn.innerHTML = '☰';
      }
    });
  }
}

/* ==========================================
   Reading Progress Bar
   ========================================== */
function initReadingProgressBar() {
  const progressBar = document.getElementById('reading-progress');
  const articleContent = document.querySelector('.article-prose');

  if (progressBar && articleContent) {
    window.addEventListener('scroll', () => {
      const totalHeight = articleContent.clientHeight;
      const offsetTop = articleContent.offsetTop;
      const scrollPos = window.scrollY - offsetTop;
      
      let progress = 0;
      if (scrollPos > 0) {
        progress = (scrollPos / (totalHeight - window.innerHeight * 0.5)) * 100;
        progress = Math.min(100, Math.max(0, progress));
      }
      
      progressBar.style.width = `${progress}%`;
    });
  }
}

/* ==========================================
   Table of Contents Active Link (ScrollSpy)
   ========================================== */
function initTableOfContents() {
  const tocLinks = document.querySelectorAll('.toc-link');
  const headings = document.querySelectorAll('.article-prose h2, .article-prose h3');

  if (tocLinks.length > 0 && headings.length > 0) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.getAttribute('id');
          tocLinks.forEach(link => {
            if (link.getAttribute('href') === `#${id}`) {
              link.classList.add('active');
            } else {
              link.classList.remove('active');
            }
          });
        }
      });
    }, { rootMargin: '-80px 0px -70% 0px' });

    headings.forEach(h => observer.observe(h));
  }
}

/* ==========================================
   Category & Search Filtering
   ========================================== */
function initCategoryFilters() {
  const filterButtons = document.querySelectorAll('.filter-btn');
  const searchInput = document.querySelector('.search-input');
  const articleCards = document.querySelectorAll('.filterable-card');

  if (filterButtons.length > 0 || searchInput) {
    function filterCards() {
      const activeBtn = document.querySelector('.filter-btn.active');
      const selectedCategory = activeBtn ? activeBtn.getAttribute('data-filter') : 'all';
      const searchTerm = searchInput ? searchInput.value.toLowerCase().trim() : '';

      articleCards.forEach(card => {
        const cardCategory = card.getAttribute('data-category');
        const cardTitle = card.querySelector('.article-card-title')?.textContent.toLowerCase() || '';
        const cardExcerpt = card.querySelector('.article-card-excerpt')?.textContent.toLowerCase() || '';
        
        const matchesCategory = selectedCategory === 'all' || cardCategory === selectedCategory;
        const matchesSearch = searchTerm === '' || cardTitle.includes(searchTerm) || cardExcerpt.includes(searchTerm);

        if (matchesCategory && matchesSearch) {
          card.style.display = 'flex';
          card.style.animation = 'fadeIn 0.3s ease forwards';
        } else {
          card.style.display = 'none';
        }
      });
    }

    filterButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        filterButtons.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        filterCards();
      });
    });

    if (searchInput) {
      searchInput.addEventListener('input', filterCards);
    }
  }
}

/* ==========================================
   FAQ Accordion
   ========================================== */
function initFaqAccordion() {
  const faqQuestions = document.querySelectorAll('.faq-question');

  faqQuestions.forEach(question => {
    question.addEventListener('click', () => {
      const item = question.parentElement;
      const isActive = item.classList.contains('active');

      // Optional: Close others
      document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));

      if (!isActive) {
        item.classList.add('active');
      }
    });
  });
}

/* ==========================================
   Interactive Form Feedback
   ========================================== */
function initInteractiveForms() {
  const newsletterForms = document.querySelectorAll('.newsletter-form');
  const contactForm = document.querySelector('.contact-form');

  newsletterForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const input = form.querySelector('input[type="email"]');
      if (input && input.value) {
        showToast(`🎉 Subscribed! Welcome to our publication.`);
        input.value = '';
      }
    });
  });

  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      showToast(`✉️ Message sent successfully! We'll reply within 24 hours.`);
      contactForm.reset();
    });
  }
}

/* ==========================================
   Share Buttons
   ========================================== */
function initShareButtons() {
  const shareButtons = document.querySelectorAll('.share-btn');
  shareButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const platform = btn.getAttribute('data-platform');
      const url = encodeURIComponent(window.location.href);
      const title = encodeURIComponent(document.title);

      if (platform === 'twitter') {
        window.open(`https://twitter.com/intent/tweet?text=${title}&url=${url}`, '_blank');
      } else if (platform === 'linkedin') {
        window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}`, '_blank');
      } else if (platform === 'copy') {
        navigator.clipboard.writeText(window.location.href).then(() => {
          showToast(`📋 Link copied to clipboard!`);
        });
      }
    });
  });
}

/* ==========================================
   Toast Notification System
   ========================================== */
function showToast(message) {
  let toast = document.querySelector('.toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  toast.textContent = message;
  toast.classList.add('show');

  setTimeout(() => {
    toast.classList.remove('show');
  }, 3500);
}
