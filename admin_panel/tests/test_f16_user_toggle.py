"""
F-16: ユーザー有効/無効トグル (UserToggleActiveView) の単体テスト
対象ビュー : admin_panel.views.UserToggleActiveView
URL name  : user_toggle_active  ->  /admin-panel/users/<pk>/toggle-active/

仕様:
  - POST のみ受付
  - 管理者のみ操作可
  - is_active を反転させる（True -> False / False -> True）
  - 自分自身は無効化できない（エラーメッセージを表示しリダイレクト）
  - 成功後 -> ユーザー一覧へリダイレクト
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from accounts.models import User


class TestF16UserToggleActive(TestCase):
    """F-16 ユーザー有効/無効トグル機能のテスト"""

    def setUp(self):
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
            is_active=True,
        )
        self.target = User.objects.create_user(
            login_id="target@example.com",
            name="対象ユーザー",
            password="TargetPass123",
            role="user",
            is_active=True,
        )
        self.url = reverse("user_toggle_active", kwargs={"pk": self.target.pk})
        self.list_url = reverse("user_admin_list")
        self.client.login(username="admin@example.com", password="AdminPass123")

    # ------------------------------------------------------------------ 正常系

    def test_toggle_active_to_inactive(self):
        """正常系: is_active=True のユーザーをトグル -> is_active=False になること"""
        self.client.post(self.url)
        self.target.refresh_from_db()
        self.assertFalse(self.target.is_active)

    def test_toggle_inactive_to_active(self):
        """正常系: is_active=False のユーザーをトグル -> is_active=True になること"""
        self.target.is_active = False
        self.target.save()
        self.client.post(self.url)
        self.target.refresh_from_db()
        self.assertTrue(self.target.is_active)

    def test_toggle_redirects_to_list(self):
        """正常系: トグル成功後 -> ユーザー一覧へリダイレクトされること"""
        response = self.client.post(self.url)
        self.assertRedirects(response, self.list_url)

    def test_toggle_success_message(self):
        """正常系: トグル成功 -> 成功メッセージが設定されること"""
        response = self.client.post(self.url, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("無効化" in m or "有効化" in m for m in msgs))

    # ------------------------------------------------------------------ 異常系

    def test_cannot_deactivate_self(self):
        """異常系: 自分自身をトグル -> is_active が変化しないこと"""
        self_url = reverse("user_toggle_active", kwargs={"pk": self.admin.pk})
        self.client.post(self_url)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_cannot_deactivate_self_shows_error_message(self):
        """異常系: 自分自身をトグル -> エラーメッセージが設定されること"""
        self_url = reverse("user_toggle_active", kwargs={"pk": self.admin.pk})
        response = self.client.post(self_url, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any("自分自身" in m for m in msgs))

    def test_cannot_deactivate_self_redirects_to_list(self):
        """異常系: 自分自身をトグル -> ユーザー一覧へリダイレクトされること"""
        self_url = reverse("user_toggle_active", kwargs={"pk": self.admin.pk})
        response = self.client.post(self_url)
        self.assertRedirects(response, self.list_url)

    def test_nonexistent_user_returns_404(self):
        """異常系: 存在しない pk -> 404 が返ること"""
        url = reverse("user_toggle_active", kwargs={"pk": 9999})
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
