/* ----------------------------------------------------------------------------------------
    ES PARA EL SIDEBAR
------------------------------------------------------------------------------------------*/

document.querySelectorAll('[data-bs-toggle="collapse"]').forEach((trigger) => {

    const target = document.querySelector(trigger.getAttribute('href'));
    const icon = trigger.querySelector('.chevron');

    if (!target || !icon) return;

    target.addEventListener('show.bs.collapse', () => {
        icon.style.transform = 'rotate(180deg)';
    });

    target.addEventListener('hide.bs.collapse', () => {
        icon.style.transform = 'rotate(0deg)';
    });

});




//Esto es para la responsividad
document.addEventListener('DOMContentLoaded', function () {

    var body = document.body;
    var toggleBtn = document.getElementById('sidebarToggle');
    var backdrop = document.getElementById('sidebarBackdrop');

    // Bootstrap usa el breakpoint "lg" = 992px. Por debajo de eso,
    // el sidebar se comporta como panel flotante (móvil/tablet).
    function isMobile() {
        return window.innerWidth < 992;
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function () {
            if (isMobile()) {
                body.classList.toggle('sidebar-mobile-open');
            } else {
                body.classList.toggle('sidebar-collapsed');
            }
        });
    }

    if (backdrop) {
        backdrop.addEventListener('click', function () {
            body.classList.remove('sidebar-mobile-open');
        });
    }

    // Evita quedar en un estado mixto si el usuario redimensiona la ventana
    // (ej. pasa de móvil a desktop con el menú abierto)
    window.addEventListener('resize', function () {
        if (isMobile()) {
            body.classList.remove('sidebar-collapsed');
        } else {
            body.classList.remove('sidebar-mobile-open');
        }
    });

});