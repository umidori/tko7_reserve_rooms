"""
F-14: ユーザー一覧表示 (UserListView) の単体テスト
対象ビュー : admin_panel.views.UserListView
URL name  : user_admin_list  ->  /admin-panel/users/

仕様:
  - 管理者 (role='admin') のみアクセス可
  - 全ユーザーを一覧表示（ページネーション 20件）
  - 氏名での部分一致検索（?q=）
  - 非管理者 -> 403  /  未認証 -> ログインへリダイレクト
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User


class TestF14UserList(TestCase):
    """F-14 ユーザー一覧表示機能のテスト"""

    def setUp(self):
        self.url = reverse("user_admin_list")
        self.login_url = "/accounts/login/"

        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.regular_user = User.objects.create_user(
            login_id="user@example.com",
            name="一般ユーザー",
            password="UserPass123",
            role="user",
        )
        self.client.login(username="admin@example.com", password="AdminPass123")

    # ------------------------------------------------------------------ 正常系

    def test_user_list_returns_200(self):
        """正常系: 管理者でアクセス -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_user_list_shows_all_users(self):
        """正常系: 全ユーザーがコンテキストに含まれること"""
        response = self.client.get(self.url)
        users = list(response.context["users"])
        self.assertIn(self.admin, users)
        self.assertIn(self.regular_user, users)

    def test_user_list_shows_user_name(self):
        """正常系: ユーザー名がページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "一般ユーザー")

    def test_user_list_shows_login_id(self):
        """正常系: ログインIDがページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "user@example.com")

    def test_search_by_name_filters_results(self):
        """正常系: ?q= で氏名の部分一致検索ができること"""
        response = self.client.get(self.url, {"q": "一般"})
        users = list(response.context["users"])
        self.assertIn(self.regular_user, users)
        self.assertNotIn(self.admin, users)

    def test_search_no_match_returns_empty(self):
        """正常系: 検索条件に一致するユーザーがいない -> 0件になること"""
        response = self.client.get(self.url, {"q": "存在しない名前"})
        users = list(response.context["users"])
        self.assertEqual(len(users), 0)

    def test_search_query_in_context(self):
        """正常系: 検索キーワード q がコンテキストに含まれること"""
        response = self.client.get(self.url, {"q": "一般"})
        self.assertEqual(response.context["q"], "一般")

    def test_total_count_in_context(self):
        """正常系: total_count に全ユーザー件数が格納されること"""
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_count"], 2)

    def test_user_list_with_department(self):
        """正常系: 所属部署ありユーザーが一覧に表示されること"""
        dept = Department.objects.create(name="営業部")
        dept_user = User.objects.create_user(
            login_id="dept@example.com",
            name="部署付きユーザー",
            password="Pass123",
            role="user",
            department=dept,
        )
        response = self.client.get(self.url)
        self.assertContains(response, "部署付きユーザー")

    # ------------------------------------------------------------------ 異常系

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーでアクセス -> 403 が返ること"""
        self.client.login(username="user@example.com", password="UserPass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            "{}?next={}".format(self.login_url, self.url),
        )
