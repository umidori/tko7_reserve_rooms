document.addEventListener('DOMContentLoaded', function () {
    const toast = document.getElementById('toast');
    if (!toast) return;

    // クリックで消す（フェードアウト）
    toast.addEventListener('click', function () {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 500);
    });

    // 5秒後に自動で消す
    setTimeout(function () {
        toast.classList.add('hide');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
});