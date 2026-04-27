"""
F-05: 予約コマのクリック表示（カレンダーポップアップ）の単体テスト
対象ビュー : reservations.views.CalendarView（サーバーサイドのデータ検証）
URL name  : calendar  →  /calendar/

F-05 はフロントエンド（JavaScript）による UI インタラクションだが、
本テストでは「ポップアップが動作するために必要なサーバーサイドのデータ」が
カレンダーページに正しく含まれることを検証する。
"""

from datetime import date, datetime, time

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF05CalendarPopup(TestCase):
    """F-05 予約コマのクリック表示（サーバーサイド検証）"""

    def setUp(self):
        self.url = reverse("calendar")
        self.today = date.today()
        self.date_param = self.today.strftime("%Y-%m-%d")

        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password="TestPass123",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)

        # 当日 10:00〜11:00 の予約
        start_at = timezone.make_aware(datetime.combine(self.today, time(10, 0)))
        end_at = timezone.make_aware(datetime.combine(self.today, time(11, 0)))
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="テスト会議",
            start_at=start_at,
            end_at=end_at,
            is_cancelled=False,
        )

        self.client.login(username="test@example.com", password="TestPass123")

    def _get_calendar(self):
        return self.client.get(self.url, {"date": self.date_param, "filter": "all"})

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_reservation_block_has_data_reservation_id(self):
        """正常系: 予約ブロックに data-reservation-id 属性が含まれること"""
        response = self._get_calendar()
        self.assertContains(
            response,
            f'data-reservation-id="{self.reservation.id}"',
        )

    def test_reservation_block_has_data_title(self):
        """正常系: 予約ブロックに data-title（件名）属性が含まれること"""
        response = self._get_calendar()
        self.assertContains(response, 'data-title="テスト会議"')

    def test_reservation_block_has_data_reserved_by(self):
        """正常系: 予約ブロックに data-reserved-by（予約者名）属性が含まれること"""
        response = self._get_calendar()
        self.assertContains(response, 'data-reserved-by="テストユーザー"')

    def test_reservation_block_has_data_start_and_end(self):
        """正常系: 予約ブロックに data-start / data-end（時刻）属性が含まれること"""
        response = self._get_calendar()
        content = response.content.decode("utf-8")
        self.assertIn('data-start="10:00"', content)
        self.assertIn('data-end="11:00"', content)

    def test_modal_detail_link_exists_in_page(self):
        """正常系: 予約詳細モーダルの「詳細を見る」リンク要素がページに存在すること"""
        response = self._get_calendar()
        self.assertContains(response, "modal-detail-link")
        self.assertContains(response, "詳細を見る")

    def test_empty_cell_has_reservation_create_url(self):
        """正常系: 空きコマに予約作成画面（/reservations/create/）への URL が含まれること"""
        response = self._get_calendar()
        self.assertContains(response, "/reservations/create/")

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_cancelled_reservation_not_shown_in_calendar(self):
        """異常系: キャンセル済み予約は予約ブロックとしてカレンダーに表示されないこと"""
        self.reservation.is_cancelled = True
        self.reservation.save()
        response = self._get_calendar()
        self.assertNotContains(
            response,
            f'data-reservation-id="{self.reservation.id}"',
        )
