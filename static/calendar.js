/* ===== ナビゲーションメニュー ===== */
function toggleNavMenu(e) {
    e.stopPropagation();
    document.getElementById('navMenu').classList.toggle('open');
}
document.addEventListener('click', function () {
    document.getElementById('navMenu').classList.remove('open');
});

/* ===== 予約詳細モーダル ===== */
function showReservationModal(el) {
    document.getElementById('modal-title').textContent       = el.dataset.title;
    document.getElementById('modal-reserved-by').textContent = el.dataset.reservedBy;
    document.getElementById('modal-time').textContent        = el.dataset.start + ' 〜 ' + el.dataset.end;
    document.getElementById('modal-detail-link').href        = '/reservations/' + el.dataset.reservationId + '/';
    document.getElementById('reservationModal').classList.add('open');
}

function closeModal() {
    document.getElementById('reservationModal').classList.remove('open');
}

function closeModalOnOverlay(e) {
    if (e.target === document.getElementById('reservationModal')) closeModal();
}
