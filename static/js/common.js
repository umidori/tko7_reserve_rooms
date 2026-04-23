document.addEventListener('DOMContentLoaded', function () {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.addEventListener('click', function () {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 500);
    });

    setTimeout(function () {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
});
