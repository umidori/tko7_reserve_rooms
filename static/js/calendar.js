/* ===== ナビゲーションメニュー ===== */
function toggleNavMenu(e) {
  e.stopPropagation();
  document.getElementById("navMenu").classList.toggle("open");
}

function toggleAdminSubmenu(e) {
  // 親メニューへの伝播を止めてメニューが閉じないようにする
  e.stopPropagation();
  const submenu = document.getElementById("adminSubmenu");
  const arrow = document.getElementById("adminArrow");
  if (submenu) submenu.classList.toggle("open");
  if (arrow) arrow.classList.toggle("open");
}

// メニュー外クリック時のみ閉じる（contains チェックで内部クリックを除外）
document.addEventListener("click", function (e) {
  const navMenu = document.getElementById("navMenu");
  const dotsBtn = document.querySelector(".dots-btn");

  // クリック対象がメニュー内・dots-btn内であれば何もしない
  if (
    (navMenu && navMenu.contains(e.target)) ||
    (dotsBtn && dotsBtn.contains(e.target))
  ) {
    return;
  }

  // メニュー外クリック → すべて閉じる
  if (navMenu) navMenu.classList.remove("open");
  const submenu = document.getElementById("adminSubmenu");
  const arrow = document.getElementById("adminArrow");
  if (submenu) submenu.classList.remove("open");
  if (arrow) arrow.classList.remove("open");
});

/* ===== 予約詳細モーダル ===== */
function showReservationModal(el) {
  document.getElementById("modal-title").textContent = el.dataset.title;
  document.getElementById("modal-reserved-by").textContent =
    el.dataset.reservedBy;
  document.getElementById("modal-time").textContent =
    el.dataset.start + " 〜 " + el.dataset.end;
  document.getElementById("modal-detail-link").href =
    "/reservations/" + el.dataset.reservationId + "/";
  document.getElementById("reservationModal").classList.add("open");
}

function closeModal() {
  document.getElementById("reservationModal").classList.remove("open");
}

function closeModalOnOverlay(e) {
  if (e.target === document.getElementById("reservationModal")) closeModal();
}
