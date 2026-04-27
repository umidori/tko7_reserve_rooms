"""
F-03: パスワード変更 (CustomPasswordChangeView) の単体テスト
対象ビュー : accounts.views.CustomPasswordChangeView
URL name  : password_change  →  /accounts/password_change/
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class TestF03PasswordChange(TestCase):
    """F-03 パスワード変更機能のテスト"""

    OLD_PASSWORD = "OldPass123"
    NEW_PASSWORD = "NewPass456"

    def setUp(self):
        self.url = reverse("password_change")
        self.success_url = reverse(
            "home"
        )  # '/' （CustomPasswordChangeView.success_url）
        self.login_url = "/accounts/login/"
        self.user = User.objects.create_user(
            login_id="test@example.com",
            name="テストユーザー",
            password=self.OLD_PASSWORD,
        )
        # パスワード変更には事前ログインが必要
        self.client.login(username="test@example.com", password=self.OLD_PASSWORD)

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_password_change_success_redirects_to_home(self):
        """正常系: 正しい現在PW・新PW・確認PWを入力 → ホーム画面（/）へリダイレクトされること"""
        response = self.client.post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password1": self.NEW_PASSWORD,
                "new_password2": self.NEW_PASSWORD,
            },
        )
        self.assertRedirects(response, self.success_url)

    def test_password_change_success_message_is_set(self):
        """正常系: パスワード変更成功時に完了メッセージがセットされること"""
        response = self.client.post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password1": self.NEW_PASSWORD,
                "new_password2": self.NEW_PASSWORD,
            },
            follow=True,
        )
        messages = list(response.context["messages"])
        self.assertTrue(
            any("パスワードを変更しました。" in str(m) for m in messages),
            msg="成功メッセージが表示されていません",
        )

    def test_new_password_can_login_after_change(self):
        """正常系: パスワード変更後に新しいPWでログインできること"""
        self.client.post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password1": self.NEW_PASSWORD,
                "new_password2": self.NEW_PASSWORD,
            },
        )
        self.client.logout()
        login_result = self.client.login(
            username="test@example.com",
            password=self.NEW_PASSWORD,
        )
        self.assertTrue(login_result, msg="新しいパスワードでのログインが失敗しました")

    def test_old_password_cannot_login_after_change(self):
        """正常系: パスワード変更後に旧PWではログインできないこと"""
        self.client.post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password1": self.NEW_PASSWORD,
                "new_password2": self.NEW_PASSWORD,
            },
        )
        self.client.logout()
        login_result = self.client.login(
            username="test@example.com",
            password=self.OLD_PASSWORD,
        )
        self.assertFalse(login_result, msg="旧パスワードでログインできてしまいました")

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_wrong_old_password_shows_error(self):
        """異常系: 現在のパスワードが不一致 → フォームエラーになること"""
        response = self.client.post(
            self.url,
            {
                "old_password": "WrongOldPass1",
                "new_password1": self.NEW_PASSWORD,
                "new_password2": self.NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context["form"].is_valid(),
            msg="現在のパスワード不一致でもフォームが通過してしまいました",
        )

    def test_new_password_too_short_shows_error(self):
        """異常系: 新パスワードが7文字以下 → バリデーションエラーになること（8文字以上必須）"""
        response = self.client.post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password1": "Ab12345",  # 7文字
                "new_password2": "Ab12345",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context["form"].is_valid(),
            msg="7文字パスワードでもバリデーションが通過してしまいました",
        )

    def test_password_confirm_mismatch_shows_error(self):
        """異常系: 確認パスワードが不一致 → バリデーションエラーになること"""
        response = self.client.post(
            self.url,
            {
                "old_password": self.OLD_PASSWORD,
                "new_password1": self.NEW_PASSWORD,
                "new_password2": "DifferentPass789",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            response.context["form"].is_valid(),
            msg="確認パスワード不一致でもバリデーションが通過してしまいました",
        )

    def test_unauthenticated_access_redirects_to_login(self):
        """異常系: 未ログイン状態でパスワード変更画面へアクセス → ログイン画面へリダイレクト"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f"{self.login_url}?next={self.url}",
        )
