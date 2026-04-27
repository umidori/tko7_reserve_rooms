"""
F-13: 重複予約チェック (ReservationForm.clean) の単体テスト
対象ロジック : reservations.forms.ReservationForm.clean
利用画面     : 予約作成 (F-09) / 予約編集 (F-11)

仕様:
  - 同一会議室・同一日時で 1 分でも重複する予約は登録・編集を拒否
  - 重複判定: 既存.start_at < 新規.end_at AND 既存.end_at > 新規.start_at
  - キャンセル済み予約 (is_cancelled=True) は重複カウントしない
  - 編集時は自分自身の予約を除外してチェック
  - 別会議室の予約とは重複しない
"""

from datetime import date, datetime, time, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


def _tomorrow():
    return date.today() + timedelta(days=1)


def _make_aware(d, t):
    return timezone.make_aware(datetime.combine(d, t))


class TestF13DuplicateCheck(TestCase):
    """F-13 重複予約チェックのテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.other_room = Room.objects.create(
            name="会議室B", capacity=5, is_active=True
        )
        self.create_url = reverse("reservation_create")
        self.future_date = _tomorrow()
        self.future_date_str = self.future_date.strftime("%Y-%m-%d")
        self.client.login(username="test@example.com", password="TestPass123")

        # 既存予約: 翌日 10:00-11:00
        self.existing = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="既存の会議",
            start_at=_make_aware(self.future_date, time(10, 0)),
            end_at=_make_aware(self.future_date, time(11, 0)),
            is_cancelled=False,
        )

    def _post_create(self, start_time, end_time, room=None):
        return self.client.post(
            self.create_url,
            {
                "room": (room or self.room).id,
                "title": "新規会議",
                "participants": "",
                "notes": "",
                "reserve_date": self.future_date_str,
                "start_time": start_time,
                "end_time": end_time,
            },
        )

    # ------------------------------------------------------------------ 正常系（重複なし）

    def test_no_overlap_after_existing_succeeds(self):
        """正常系: 既存終了後 (11:00-12:00) -> 重複なしで登録成功すること"""
        self._post_create("11:00", "12:00")
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 2)

    def test_no_overlap_before_existing_succeeds(self):
        """正常系: 既存開始前 (09:00-10:00) -> 重複なしで登録成功すること"""
        self._post_create("09:00", "10:00")
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 2)

    def test_adjacent_end_equals_existing_start_no_overlap(self):
        """正常系: 新規終了 = 既存開始 (09:00-10:00) -> 境界値は重複なしであること"""
        self._post_create("09:00", "10:00")
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 2)

    def test_adjacent_start_equals_existing_end_no_overlap(self):
        """正常系: 新規開始 = 既存終了 (11:00-12:00) -> 境界値は重複なしであること"""
        self._post_create("11:00", "12:00")
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 2)

    def test_different_room_no_overlap(self):
        """正常系: 別会議室の同一時間帯 -> 重複なしで登録成功すること"""
        self._post_create("10:00", "11:00", room=self.other_room)
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 2)

    def test_cancelled_existing_not_counted_as_overlap(self):
        """正常系: 既存予約がキャンセル済み -> 同一時間帯でも重複なしで登録成功すること"""
        self.existing.is_cancelled = True
        self.existing.save()
        self._post_create("10:00", "11:00")
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 1)

    def test_edit_self_same_time_succeeds(self):
        """正常系: 編集時に自分自身と同一時間帯 -> 自己除外で編集成功すること"""
        edit_url = reverse("reservation_edit", kwargs={"pk": self.existing.pk})
        response = self.client.post(
            edit_url,
            {
                "room": self.room.id,
                "title": "更新後の会議",
                "participants": "",
                "notes": "",
                "reserve_date": self.future_date_str,
                "start_time": "10:00",
                "end_time": "11:00",
            },
        )
        self.existing.refresh_from_db()
        self.assertEqual(self.existing.title, "更新後の会議")

    # ------------------------------------------------------------------ 異常系（重複あり）

    def test_exact_same_time_shows_error(self):
        """異常系: 完全一致 (10:00-11:00) -> 重複エラーになること"""
        response = self._post_create("10:00", "11:00")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
        self.assertEqual(Reservation.objects.filter(is_cancelled=False).count(), 1)

    def test_overlap_start_inside_existing_shows_error(self):
        """異常系: 新規開始が既存内 (10:30-11:30) -> 重複エラーになること"""
        response = self._post_create("10:30", "11:30")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_overlap_end_inside_existing_shows_error(self):
        """異常系: 新規終了が既存内 (09:30-10:30) -> 重複エラーになること"""
        response = self._post_create("09:30", "10:30")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_overlap_contains_existing_shows_error(self):
        """異常系: 新規が既存を包含 (09:00-12:00) -> 重複エラーになること"""
        response = self._post_create("09:00", "12:00")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())

    def test_overlap_error_message_shown_in_response(self):
        """異常系: 重複時にエラーメッセージがレスポンスに含まれること"""
        response = self._post_create("10:00", "11:00")
        self.assertContains(response, "既に予約されています")

    def test_edit_other_reservation_overlap_shows_error(self):
        """異常系: 編集時に別の予約と重複 -> 重複エラーになること"""
        # 別の予約を作成 (12:00-13:00)
        other_rsv = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="別の会議",
            start_at=_make_aware(self.future_date, time(12, 0)),
            end_at=_make_aware(self.future_date, time(13, 0)),
            is_cancelled=False,
        )
        # other_rsv を既存の 10:00-11:00 と重複する時間に編集しようとする
        edit_url = reverse("reservation_edit", kwargs={"pk": other_rsv.pk})
        response = self.client.post(
            edit_url,
            {
                "room": self.room.id,
                "title": "重複編集",
                "participants": "",
                "notes": "",
                "reserve_date": self.future_date_str,
                "start_time": "10:30",
                "end_time": "11:30",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_valid())
