(function () {
    const theme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.documentElement.style.backgroundColor = theme === 'dark' ? '#212529' : '#fbfbfb';
})();

function toggleDarkMode() {
    const html = document.documentElement;
    const icon = document.getElementById('theme-icon');
    const newTheme = html.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-bs-theme', newTheme);
    html.style.backgroundColor = newTheme === 'dark' ? '#212529' : '#fbfbfb';
    localStorage.setItem('theme', newTheme);

    if (icon) {
        icon.classList.replace(
            newTheme === 'dark' ? 'fa-moon' : 'fa-sun',
            newTheme === 'dark' ? 'fa-sun' : 'fa-moon'
        );
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const icon = document.getElementById('theme-icon');
    if (icon && localStorage.getItem('theme') === 'dark') {
        icon.classList.replace('fa-moon', 'fa-sun');
    }
});
