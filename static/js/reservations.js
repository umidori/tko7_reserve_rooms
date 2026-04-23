document.addEventListener('DOMContentLoaded', function () {
  const roomSelect = document.getElementById('roomSelect');

  // 要素取得
  const roomName = document.getElementById('selectedRoomName');
  const roomCapacity = document.getElementById('selectedRoomCapacity');
  const roomBuilding = document.getElementById('selectedRoomBuilding');
  const roomFloor = document.getElementById('selectedRoomFloor');

  if (!roomSelect) return;

  function updateSelectedRoom() {
    const option = roomSelect.options[roomSelect.selectedIndex];

    if (!option || !option.value) {
      roomName.textContent = '';
      roomCapacity.textContent = '';
      roomBuilding.textContent = '';
      roomFloor.textContent = '';
      return;
    }

    roomName.textContent = option.dataset.name || '-';
    roomCapacity.textContent = '収容人数：' + (option.dataset.capacity || '-') + '名';
    roomBuilding.textContent = '建物：' + (option.dataset.building || '-');
    roomFloor.textContent = option.dataset.floor
      ? option.dataset.floor + '階'
      : '-';
  }

  // イベント登録
  roomSelect.addEventListener('change', updateSelectedRoom);

  // 初期反映
  updateSelectedRoom();
});

document.addEventListener('DOMContentLoaded', function () {
    const openCancelModalBtn = document.getElementById('openCancelModal');
    const closeCancelModalBtn = document.getElementById('closeCancelModal');
    const cancelModal = document.getElementById('cancelModal');

    if (openCancelModalBtn && closeCancelModalBtn && cancelModal) {
        openCancelModalBtn.addEventListener('click', function () {
            cancelModal.hidden = false;
        });

        closeCancelModalBtn.addEventListener('click', function () {
            cancelModal.hidden = true;
        });

        cancelModal.addEventListener('click', function (event) {
            if (event.target === cancelModal) {
                cancelModal.hidden = true;
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
  const roomSelect = document.getElementById('roomSelect');

  if (!roomSelect) return;

  roomSelect.addEventListener('change', function () {
    const error = roomSelect.parentElement.querySelector('.field-error');

    if (roomSelect.value && error) {
      error.remove();
    }
  });
});

document.addEventListener('DOMContentLoaded', function () {
  const dateInput = document.querySelector('[name="reserve_date"]');

  if (!dateInput) return;

  function clearDateError() {
    const fieldBlock = dateInput.parentElement;
    const error = fieldBlock.querySelector('.field-error');

    if (dateInput.value && error) {
      error.remove();
    }
  }

  dateInput.addEventListener('change', clearDateError);
  dateInput.addEventListener('input', clearDateError);
});

document.addEventListener('DOMContentLoaded', function () {
  const titleInput = document.querySelector('[name="title"]');

  if (!titleInput) return;

  function clearTitleError() {
    const fieldBlock = titleInput.parentElement;
    const errorArea = fieldBlock.querySelector('.field-error-area');

    if (titleInput.value && errorArea) {
      errorArea.innerHTML = '';
    }
  }

  titleInput.addEventListener('input', clearTitleError);
  titleInput.addEventListener('change', clearTitleError);
});
