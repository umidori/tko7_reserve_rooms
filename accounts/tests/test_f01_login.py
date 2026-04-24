"""
F-01: ログイン (CustomLoginView) の単体テスト
対象ビュー : accounts.views.CustomLoginView
URL name  : login  →  /accounts/login/
"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class TestF01Login(TestCase):
    """F-01 ログイン機能のテスト"""

    def setUp(self):
        self.url = reverse('login')
        self.calendar_url = '/calendar/'
        # テスト用ユーザー（login_id はメールアドレス形式）
        self.user = User.objects.create_user(
            login_id='test@example.com',
            name='テストユーザー',
            password='TestPass123',
        )

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_login_success_redirects_to_calendar(self):
        """正常系: 有効なID・PWでログイン → カレンダー画面（/calendar/）へリダイレクト"""
        response = self.client.post(self.url, {
            'username': 'test@example.com',
            'password': 'TestPass123',
        })
        self.assertRedirects(response, self.calendar_url)

    def test_unauthenticated_access_redirects_to_login(self):
        """正常系: 未ログイン状態でカレンダーにアクセス → ログイン画面へリダイレクト"""
        response = self.client.get(self.calendar_url)
        self.assertRedirects(
            response,
            f'{self.url}?next={self.calendar_url}',
        )

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_login_wrong_user_id_shows_error(self):
        """異常系: 存在しないユーザーIDでログイン → エラーメッセージが表示されること"""
        response = self.client.post(self.url, {
            'username': 'nobody@example.com',
            'password': 'TestPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザーIDまたはパスワードが正しくありません。')

    def test_login_wrong_password_shows_error(self):
        """異常系: パスワード不一致でログイン → エラーメッセージが表示されること"""
        response = self.client.post(self.url, {
            'username': 'test@example.com',
            'password': 'WrongPassword',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザーIDまたはパスワードが正しくありません。')

    def test_login_inactive_user_shows_error(self):
        """異常系: is_active=False のユーザーでログイン → エラーメッセージが表示されること"""
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.url, {
            'username': 'test@example.com',
            'password': 'TestPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ユーザーIDまたはパスワードが正しくありません。')

    def test_login_empty_username_shows_validation_error(self):
        """異常系: ユーザーID空欄でフォーム送信 → バリデーションエラーが表示されること"""
        response = self.client.post(self.url, {
            'username': '',
            'password': 'TestPass123',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'このフィールドは必須です。')
