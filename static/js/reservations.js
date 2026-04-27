document.addEventListener("DOMContentLoaded", function () {
  initRoomSelect();
  initCancelModal();
  initErrorClear();
});

/* ===== 会議室選択 ===== */
function initRoomSelect() {
  const roomSelect = document.getElementById("roomSelect");
  if (!roomSelect) return;

  const roomName = document.getElementById("selectedRoomName");
  const roomCapacity = document.getElementById("selectedRoomCapacity");
  const roomBuilding = document.getElementById("selectedRoomBuilding");
  const roomFloor = document.getElementById("selectedRoomFloor");

  function update() {
    const option = roomSelect.options[roomSelect.selectedIndex];

    if (!option || !option.value) {
      roomName.textContent = "";
      roomCapacity.textContent = "";
      roomBuilding.textContent = "";
      roomFloor.textContent = "";
      return;
    }

    roomName.textContent = option.dataset.name || "-";
    roomCapacity.textContent =
      "収容人数：" + (option.dataset.capacity || "-") + "名";
    roomBuilding.textContent = "建物：" + (option.dataset.building || "-");
    roomFloor.textContent = option.dataset.floor
      ? option.dataset.floor + "階"
      : "-";
  }

  roomSelect.addEventListener("change", update);
  update();
}

/* ===== キャンセルモーダル ===== */
function initCancelModal() {
  const openBtn = document.getElementById("openCancelModal");
  const closeBtn = document.getElementById("closeCancelModal");
  const modal = document.getElementById("cancelModal");

  if (!openBtn || !closeBtn || !modal) return;

  openBtn.addEventListener("click", () => {
    modal.hidden = false;
  });

  closeBtn.addEventListener("click", () => {
    modal.hidden = true;
  });

  modal.addEventListener("click", function (e) {
    if (e.target === modal) {
      modal.hidden = true;
    }
  });
}

/* ===== エラー削除 ===== */
function initErrorClear() {
  clearError('[name="title"]');
  clearError('[name="reserve_date"]');
  clearError("#roomSelect");
}

function clearError(selector) {
  const el = document.querySelector(selector);
  if (!el) return;

  el.addEventListener("input", function () {
    const block = el.closest(".field-block");
    if (!block) return;

    const error = block.querySelector(".field-error");
    const errorArea = block.querySelector(".field-error-area");

    if (error) error.remove();
    if (errorArea) errorArea.innerHTML = "";
  });
}
