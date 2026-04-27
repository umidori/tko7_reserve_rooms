"""
F-20: 会議室利用停止/再開 (RoomToggleActiveView) の単体テスト
対象ビュー : admin_panel.views.RoomToggleActiveView
URL name  : room_toggle_active  ->  /admin-panel/rooms/<pk>/toggle-active/

仕様:
  - POST のみ受付
  - 管理者のみ操作可
  - is_active を反転（True -> False / False -> True）
  - 成功後 -> 会議室一覧へリダイレクト
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from reservations.models import Room


class TestF20RoomToggleActive(TestCase):
    """F-20 会議室利用停止/再開機能のテスト"""

    def setUp(self):
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.url = reverse("room_toggle_active", kwargs={"pk": self.room.pk})
        self.list_url = reverse("room_admin_list")
        self.client.login(username="admin@example.com", password="AdminPass123")

    # ------------------------------------------------------------------ 正常系

    def test_toggle_active_to_inactive(self):
        """正常系: is_active=True の会議室をトグル -> is_active=False になること"""
        self.client.post(self.url)
        self.room.refresh_from_db()
        self.assertFalse(self.room.is_active)

    def test_toggle_inactive_to_active(self):
        """正常系: is_active=False の会議室をトグル -> is_active=True になること"""
        self.room.is_active = False
        self.room.save()
        self.client.post(self.url)
        self.room.refresh_from_db()
        self.assertTrue(self.room.is_active)

    def test_toggle_redirects_to_list(self):
        """正常系: トグル成功後 -> 会議室一覧へリダイレクトされること"""
        response = self.client.post(self.url)
        self.assertRedirects(response, self.list_url)

    # ------------------------------------------------------------------ 異常系

    def test_nonexistent_room_returns_404(self):
        """異常系: 存在しない pk -> 404 が返ること"""
        url = reverse("room_toggle_active", kwargs={"pk": 9999})
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
