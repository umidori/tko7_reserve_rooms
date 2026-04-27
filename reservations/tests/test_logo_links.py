"""
ロゴリンク テスト
全ページのヘッダーロゴがホームページ (/) へのリンクになっていることを確認する。
対象テンプレート（代表）:
  - 日次カレンダー (calendar)
  - 会議室一覧 (rooms:room_list)
  - 予約詳細 (reservation_detail)
  - 自分の予約 (my_reservations)
  - ユーザー管理一覧 (user_admin_list)  ← 管理者ページ
  - 全予約一覧 (all_reservation_list)   ← 管理者ページ
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


HOME_URL = "/"
LOGO_LINK = 'href="{}"'.format(HOME_URL)


class TestLogoLinksUser(TestCase):
    """一般ユーザーがアクセスするページのロゴリンクテスト"""

    def setUp(self):
        self.user = User.objects.create_user(
            login_id="user@example.com",
            name="テストユーザー",
            password="TestPass123",
            role="user",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        now = timezone.now()
        self.reservation = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by="テストユーザー",
            title="テスト会議",
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=1, hours=1),
        )
        self.client.login(username="user@example.com", password="TestPass123")

    def test_calendar_logo_links_to_home(self):
        """日次カレンダーのロゴが / へリンクしていること"""
        response = self.client.get(reverse("calendar"))
        self.assertContains(response, LOGO_LINK)

    def test_room_list_logo_links_to_home(self):
        """会議室一覧のロゴが / へリンクしていること"""
        response = self.client.get(reverse("rooms:room_list"))
        self.assertContains(response, LOGO_LINK)

    def test_reservation_detail_logo_links_to_home(self):
        """予約詳細のロゴが / へリンクしていること"""
        response = self.client.get(
            reverse("reservation_detail", kwargs={"pk": self.reservation.pk})
        )
        self.assertContains(response, LOGO_LINK)

    def test_my_reservations_logo_links_to_home(self):
        """自分の予約のロゴが / へリンクしていること"""
        response = self.client.get(reverse("my_reservations"))
        self.assertContains(response, LOGO_LINK)

    def test_reservation_create_logo_links_to_home(self):
        """予約作成画面のロゴが / へリンクしていること"""
        response = self.client.get(reverse("reservation_create"))
        self.assertContains(response, LOGO_LINK)


class TestLogoLinksAdmin(TestCase):
    """管理者がアクセスするページのロゴリンクテスト"""

    def setUp(self):
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.client.login(username="admin@example.com", password="AdminPass123")

    def test_user_list_logo_links_to_home(self):
        """ユーザー管理一覧のロゴが / へリンクしていること"""
        response = self.client.get(reverse("user_admin_list"))
        self.assertContains(response, LOGO_LINK)

    def test_all_reservation_list_logo_links_to_home(self):
        """全予約一覧のロゴが / へリンクしていること"""
        response = self.client.get(reverse("all_reservation_list"))
        self.assertContains(response, LOGO_LINK)

    def test_room_admin_list_logo_links_to_home(self):
        """会議室管理一覧のロゴが / へリンクしていること"""
        response = self.client.get(reverse("room_admin_list"))
        self.assertContains(response, LOGO_LINK)

    def test_csv_import_logo_links_to_home(self):
        """CSVインポートのロゴが / へリンクしていること"""
        response = self.client.get(reverse("csv_import"))
        self.assertContains(response, LOGO_LINK)
