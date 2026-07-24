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