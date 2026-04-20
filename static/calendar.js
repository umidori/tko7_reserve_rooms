function showReservationModal(el) {
    // data-* 属性からデータを取り出す
    const id          = el.dataset.reservationId;
    const title       = el.dataset.title;
    const reservedBy  = el.dataset.reservedBy;
    const start       = el.dataset.start;
    const end         = el.dataset.end;

    // モーダルの中身を書き換える
    document.getElementById('modal-title').textContent       = title;
    document.getElementById('modal-reserved-by').textContent = reservedBy;
    document.getElementById('modal-time').textContent        = start + ' 〜 ' + end;

    // 「詳細を見る」リンクのURLを動的にセット
    document.getElementById('modal-detail-link').href = '/reservations/' + id + '/';

    // Bootstrap 5 のモーダルを表示する
    const modal = new bootstrap.Modal(document.getElementById('reservationModal'));
    modal.show();
}