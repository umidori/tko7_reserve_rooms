"""
F-19: 会議室削除 (RoomDeleteView) の単体テスト
対象ビュー : admin_panel.views.RoomDeleteView
URL name  : room_delete  ->  /admin-panel/rooms/<pk>/delete/

仕様:
  - POST のみ受付
  - 管理者のみ操作可
  - 会議室を削除（紐づく予約も CASCADE 削除）
  - 成功後 -> 会議室一覧へリダイレクト
"""

from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF19RoomDelete(TestCase):
    """F-19 会議室削除機能のテスト"""

    def setUp(self):
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.url = reverse("room_delete", kwargs={"pk": self.room.pk})
        self.list_url = reverse("room_admin_list")
        self.client.login(username="admin@example.com", password="AdminPass123")

    # ------------------------------------------------------------------ 正常系

    def test_delete_room_removes_room(self):
        """正常系: POST -> 会議室が削除されること"""
        self.client.post(self.url)
        self.assertFalse(Room.objects.filter(pk=self.room.pk).exists())

    def test_delete_room_redirects_to_list(self):
        """正常系: 削除成功後 -> 会議室一覧へリダイレクトされること"""
        response = self.client.post(self.url)
        self.assertRedirects(response, self.list_url)

    def test_delete_room_cascades_reservations(self):
        """正常系: 会議室削除時に紐づく予約も CASCADE 削除されること"""
        now = timezone.now()
        rsv = Reservation.objects.create(
            room=self.room,
            user=self.admin,
            reserved_by="管理者",
            title="テスト予約",
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=1, hours=1),
        )
        self.client.post(self.url)
        self.assertFalse(Reservation.objects.filter(pk=rsv.pk).exists())

    # ------------------------------------------------------------------ 異常系

    def test_delete_nonexistent_room_returns_404(self):
        """異常系: 存在しない pk -> 404 が返ること"""
        url = reverse("room_delete", kwargs={"pk": 9999})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_get_method_not_allowed(self):
        """異常系: GET リクエスト -> 405 Method Not Allowed が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーで POST -> 403 が返ること"""
        User.objects.create_user(
            login_id="user@example.com", name="一般", password="Pass123", role="user"
        )
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態で POST -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next={}".format(self.url),
        )
