/*
  Theme system — applied sync before CSS to prevent flash.
  Current themes: 'light' | 'dark' | 'system'
  To add a new theme: add a case in applyTheme() and a CSS block in core.css.

  Source of truth priority:
    1. data-user-theme on <html> (injected from DB by server)
    2. localStorage (for page loads before server response)
*/

(function () {
    var html = document.documentElement;
    var serverTheme = html.getAttribute('data-user-theme');
    var theme;

    if (serverTheme === 'system' || !serverTheme) {
        var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        theme = prefersDark ? 'dark' : 'light';
    } else {
        theme = serverTheme; // 'light' or 'dark' from DB
    }

    localStorage.setItem('theme', theme);
    applyTheme(theme);
})();

function applyTheme(theme) {
    var html = document.documentElement;

    html.setAttribute('data-bs-theme', theme === 'dark' ? 'dark' : 'light');

    var bodyBg = theme === 'dark' ? '#0E0C10' : '#F5F1EC';
    html.style.backgroundColor = bodyBg;

    localStorage.setItem('theme', theme);

    /* Future custom theme hook — extend here */
    /* html.setAttribute('data-theme', theme); */
}

function toggleTheme() {
    var current = localStorage.getItem('theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    updateThemeIcon(next);
    _saveThemeToDb(next);
}

function updateThemeIcon(theme) {
    var icon = document.getElementById('theme-icon');
    if (!icon) return;
    if (theme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}

function _saveThemeToDb(theme) {
    var csrf = document.getElementById('csrf_token');
    if (!csrf) return;
    fetch('/config/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrf.value,
        },
        body: JSON.stringify({ theme: theme }),
    });
}

document.addEventListener('DOMContentLoaded', function () {
    var theme = localStorage.getItem('theme') || 'light';
    updateThemeIcon(theme);
});
