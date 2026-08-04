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

// ---------------------------------------------------------------------------
// GLOBAL CONFIRMATION MODAL FOR FORMS
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', function () {
    var modalEl = document.getElementById('modalConfirmarAccion');
    if (!modalEl) return;

    var modal = new bootstrap.Modal(modalEl);
    var mensajeEl = document.getElementById('modalConfirmarAccionMensaje');
    var tituloEl = document.getElementById('modalConfirmarAccionLabel');
    var btnAceptar = document.getElementById('modalConfirmarAccionAceptar');
    var currentForm = null;

    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (form._confirmed) {
                form._confirmed = false;
                return;
            }

            event.preventDefault();
            currentForm = form;

            mensajeEl.textContent = form.dataset.confirm || '¿Confirmar esta acción?';
            tituloEl.textContent = form.dataset.confirmTitle || 'Confirmar acción';
            btnAceptar.textContent = form.dataset.confirmOkText || 'Confirmar';
            btnAceptar.className = form.dataset.confirmOkClass || 'btn btn-danger shadow-sm fw-medium';

            modal.show();
        });
    });

    btnAceptar.addEventListener('click', function () {
        if (!currentForm) return;
        currentForm._confirmed = true;
        modal.hide();
        currentForm.submit();
        currentForm = null;
    });

    function getEditConfirmMessage(trigger) {
        if (!trigger) return '¿Guardar cambios?';

        const ds = trigger.dataset;
        if (ds.usuario) {
            return `¿Guardar cambios en el usuario ${ds.usuario}?`;
        }
        if (ds.folio) {
            return `¿Guardar cambios en la orden #${ds.folio}?`;
        }
        if (ds.numero && ds.modelo) {
            return `¿Guardar cambios en el registro #${ds.numero} (${ds.modelo})?`;
        }
        if (ds.numero) {
            return `¿Guardar cambios en el registro #${ds.numero}?`;
        }
        if (ds.codigo) {
            return `¿Guardar cambios en el código ${ds.codigo}?`;
        }
        if (ds.modelo) {
            return `¿Guardar cambios en el modelo ${ds.modelo}?`;
        }
        if (ds.nombre) {
            return `¿Guardar cambios en ${ds.nombre}?`;
        }
        return '¿Guardar cambios?';
    }

    document.querySelectorAll('.modal').forEach(function (modalEl) {
        modalEl.addEventListener('show.bs.modal', function (event) {
            const trigger = event.relatedTarget;
            const form = modalEl.querySelector('form#formEditar');
            if (!form || !trigger) return;
            form.dataset.confirm = getEditConfirmMessage(trigger);
        });
    });
});

// ---------------------------------------------------------------------------
// ATAJO "/" PARA ENFOCAR EL BUSCADOR (RNF03 Atajos de teclado)
// ---------------------------------------------------------------------------
document.addEventListener('keydown', function (event) {
    if (event.key !== '/') return;

    var activo = document.activeElement;
    var yaEscribiendo = activo && (activo.tagName === 'INPUT' || activo.tagName === 'TEXTAREA' || activo.tagName === 'SELECT' || activo.isContentEditable);
    if (yaEscribiendo) return;

    // La plantilla de ensamblaje usa name="q"; el resto usa name="buscar".
    var buscador = document.querySelector('input[name="buscar"], input[name="q"]');
    if (!buscador) return;

    event.preventDefault();
    buscador.focus();
});