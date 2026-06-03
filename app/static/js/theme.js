/*
  Theme system — applied sync before CSS to prevent flash.
  Current themes: 'light' | 'dark'
  To add a new theme: add a case in applyTheme() and a CSS block in core.css.
*/

(function () {
    var theme = localStorage.getItem('theme') || 'light';
    applyTheme(theme);
})();

function applyTheme(theme) {
    var html = document.documentElement;

    /* Bootstrap dark mode toggle */
    html.setAttribute('data-bs-theme', theme === 'dark' ? 'dark' : 'light');

    /* Instant body bg to prevent flash */
    var bodyBg = theme === 'dark' ? '#12141a' : '#f0f2f5';
    html.style.backgroundColor = bodyBg;

    /* Future custom theme hook — extend here */
    /* html.setAttribute('data-theme', theme); */

    localStorage.setItem('theme', theme);
}

function toggleTheme() {
    var current = localStorage.getItem('theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    updateThemeIcon(next);
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

document.addEventListener('DOMContentLoaded', function () {
    var theme = localStorage.getItem('theme') || 'light';
    updateThemeIcon(theme);
});
