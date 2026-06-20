// Guild Atelier — EN / VI language toggle
(function () {
  var STORAGE_KEY = 'guild-atelier-lang';
  var html = document.documentElement;
  var toggleBtn = document.getElementById('lang-toggle');
  var nodes = document.querySelectorAll('[data-en][data-vi]');

  function applyLang(lang) {
    nodes.forEach(function (el) {
      el.textContent = el.getAttribute('data-' + lang);
    });
    html.setAttribute('lang', lang === 'vi' ? 'vi' : 'en');
    html.setAttribute('data-current-lang', lang);
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) { /* storage unavailable, ignore */ }
  }

  function getInitialLang() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'en' || saved === 'vi') return saved;
    } catch (e) { /* ignore */ }
    // Fall back to browser language
    var nav = (navigator.language || '').toLowerCase();
    return nav.indexOf('vi') === 0 ? 'vi' : 'en';
  }

  var currentLang = getInitialLang();
  applyLang(currentLang);

  toggleBtn.addEventListener('click', function () {
    currentLang = currentLang === 'en' ? 'vi' : 'en';
    applyLang(currentLang);
  });
})();
