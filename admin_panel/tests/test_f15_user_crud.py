"""
F-15: ユーザー追加・編集 (UserCreateView / UserUpdateView) の単体テスト
対象ビュー : admin_panel.views.UserCreateView / UserUpdateView
URL name  : user_create  ->  /admin-panel/users/create/
           user_edit    ->  /admin-panel/users/<pk>/edit/

仕様:
  - 管理者のみ操作可
  - 追加: 初期パスワード 'Bold1234'・is_active=True で登録
  - 追加: login_id 重複 -> バリデーションエラー
  - 編集: 氏名・権限・所属を変更可（login_id は変更不可）
  - GET -> ユーザー一覧へリダイレクト
  - 成功後 -> ユーザー一覧へリダイレクト
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User


class TestF15UserCreate(TestCase):
    """F-15 ユーザー追加機能のテスト"""

    def setUp(self):
        self.url = reverse("user_create")
        self.list_url = reverse("user_admin_list")
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.client.login(username="admin@example.com", password="AdminPass123")

    def _valid_post(self, **overrides):
        data = {
            "login_id": "new@example.com",
            "name": "新ユーザー",
            "role": "user",
            "department": "",
        }
        data.update(overrides)
        return data

    # ------------------------------------------------------------------ 正常系

    def test_create_user_success(self):
        """正常系: 有効な入力で POST -> ユーザーが1件作成されること"""
        self.client.post(self.url, self._valid_post())
        self.assertTrue(User.objects.filter(login_id="new@example.com").exists())

    def test_create_user_redirects_to_list(self):
        """正常系: 作成成功後 -> ユーザー一覧へリダイレクトされること"""
        response = self.client.post(self.url, self._valid_post())
        self.assertRedirects(response, self.list_url)

    def test_create_user_sets_initial_password(self):
        """正常系: 作成されたユーザーの初期パスワードが 'Bold1234' であること"""
        self.client.post(self.url, self._valid_post())
        created = User.objects.get(login_id="new@example.com")
        self.assertTrue(created.check_password("Bold1234"))

    def test_create_user_sets_is_active_true(self):
        """正常系: 作成されたユーザーの is_active が True であること"""
        self.client.post(self.url, self._valid_post())
        created = User.objects.get(login_id="new@example.com")
        self.assertTrue(created.is_active)

    def test_create_user_with_department(self):
        """正常系: 所属を指定してユーザーを作成できること"""
        dept = Department.objects.create(name="営業部")
        self.client.post(self.url, self._valid_post(department=dept.pk))
        created = User.objects.get(login_id="new@example.com")
        self.assertEqual(created.department, dept)

    def test_get_redirects_to_list(self):
        """正常系: GET リクエスト -> ユーザー一覧へリダイレクトされること"""
        response = self.client.get(self.url)
        self.assertRedirects(response, self.list_url)

    # ------------------------------------------------------------------ 異常系

    def test_duplicate_login_id_shows_error(self):
        """異常系: 既存の login_id -> バリデーションエラーになり作成されないこと"""
        User.objects.create_user(
            login_id="dup@example.com", name="既存", password="Pass123"
        )
        response = self.client.post(
            self.url, self._valid_post(login_id="dup@example.com")
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(login_id="dup@example.com").count(), 1)

    def test_empty_name_shows_error(self):
        """異常系: 氏名が空欄 -> バリデーションエラーになること"""
        response = self.client.post(self.url, self._valid_post(name=""))
        self.assertEqual(response.status_code, 200)

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーで POST -> 403 が返ること"""
        User.objects.create_user(
            login_id="user@example.com", name="一般", password="Pass123", role="user"
        )
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.url, self._valid_post())
        self.assertEqual(response.status_code, 403)


class TestF15UserUpdate(TestCase):
    """F-15 ユーザー編集機能のテスト"""

    def setUp(self):
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.target = User.objects.create_user(
            login_id="target@example.com",
            name="編集対象",
            password="Pass123",
            role="user",
        )
        self.url = reverse("user_edit", kwargs={"pk": self.target.pk})
        self.list_url = reverse("user_admin_list")
        self.client.login(username="admin@example.com", password="AdminPass123")

    def _valid_post(self, **overrides):
        data = {
            "name": "更新後の氏名",
            "role": "user",
            "department": "",
        }
        data.update(overrides)
        return data

    # ------------------------------------------------------------------ 正常系

    def test_update_user_name(self):
        """正常系: 氏名を変更して保存 -> 氏名が更新されること"""
        self.client.post(self.url, self._valid_post(name="更新後の氏名"))
        self.target.refresh_from_db()
        self.assertEqual(self.target.name, "更新後の氏名")

    def test_update_user_role(self):
        """正常系: 権限を admin に変更して保存 -> 権限が更新されること"""
        self.client.post(self.url, self._valid_post(role="admin"))
        self.target.refresh_from_db()
        self.assertEqual(self.target.role, "admin")

    def test_update_user_redirects_to_list(self):
        """正常系: 更新成功後 -> ユーザー一覧へリダイレクトされること"""
        response = self.client.post(self.url, self._valid_post())
        self.assertRedirects(response, self.list_url)

    def test_update_does_not_change_login_id(self):
        """正常系: 編集フォームに login_id フィールドがないため login_id は変化しないこと"""
        self.client.post(self.url, self._valid_post())
        self.target.refresh_from_db()
        self.assertEqual(self.target.login_id, "target@example.com")

    def test_get_redirects_to_list(self):
        """正常系: GET リクエスト -> ユーザー一覧へリダイレクトされること"""
        response = self.client.get(self.url)
        self.assertRedirects(response, self.list_url)

    # ------------------------------------------------------------------ 異常系

    def test_nonexistent_user_returns_404(self):
        """異常系: 存在しない pk -> 404 が返ること"""
        url = reverse("user_edit", kwargs={"pk": 9999})
        response = self.client.post(url, self._valid_post())
        self.assertEqual(response.status_code, 404)

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーで編集 POST -> 403 が返ること"""
        User.objects.create_user(
            login_id="user@example.com", name="一般", password="Pass123", role="user"
        )
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.url, self._valid_post())
        self.assertEqual(response.status_code, 403)
