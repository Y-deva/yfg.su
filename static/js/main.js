// Бургер-меню
document.addEventListener('DOMContentLoaded', function() {
    const burgerBtn = document.getElementById('burgerBtn');
    const burgerDropdown = document.getElementById('burgerDropdown');
    const overlay = document.createElement('div');
    overlay.className = 'burger-overlay';
    document.body.appendChild(overlay);

    function toggleMenu() {
        burgerDropdown.classList.toggle('open');
        overlay.classList.toggle('show');
        burgerBtn.classList.toggle('open');
        document.body.style.overflow = burgerDropdown.classList.contains('open') ? 'hidden' : '';
    }

    burgerBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        toggleMenu();
    });

    overlay.addEventListener('click', toggleMenu);

    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && burgerDropdown.classList.contains('open')) {
            toggleMenu();
        }
    });

    // Закрытие при клике на ссылку
    document.querySelectorAll('.burger-menu-section a').forEach(link => {
        link.addEventListener('click', function() {
            if (burgerDropdown.classList.contains('open')) toggleMenu();
        });
    });

    // Тосты (автоматическое исчезновение)
    document.querySelectorAll('.toast').forEach(toast => {
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    });
});