"""
F-17: CSVインポート (CSVImportView / CSVImportExecuteView) の単体テスト
対象ビュー : admin_panel.views.CSVImportView / CSVImportExecuteView
URL name  : csv_import         ->  /admin-panel/users/csv-import/
           csv_import_execute  ->  /admin-panel/users/csv-import/execute/

仕様:
  - 管理者のみ操作可
  - CSV列: login_id, name, role, dept_name（1行目はヘッダー）
  - アップロード後にプレビューを表示（セッションに保存）
  - バリデーション: 必須項目・role 値・login_id 重複
  - 実行で有効行のみ bulk_create（初期PW: Bold1234）
  - dept_name が存在しなければ自動作成
  - セッションなしで実行 -> csv_import へリダイレクト
"""
import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.contrib.messages import get_messages

from accounts.models import Department, User


def _make_csv(*rows, header='login_id,name,role,dept_name'):
    lines = [header] + list(rows)
    return SimpleUploadedFile(
        'users.csv',
        '\n'.join(lines).encode('utf-8'),
        content_type='text/csv',
    )


class TestF17CSVImportView(TestCase):
    """F-17 CSVインポート（プレビュー）のテスト"""

    def setUp(self):
        self.url = reverse('csv_import')
        self.admin = User.objects.create_user(
            login_id='admin@example.com',
            name='管理者',
            password='AdminPass123',
            role='admin',
        )
        self.client.login(username='admin@example.com', password='AdminPass123')

    # ------------------------------------------------------------------ 正常系

    def test_get_returns_200(self):
        """正常系: GET /admin-panel/users/csv-import/ -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_get_clears_session(self):
        """正常系: GET でセッションの csv_preview_data がクリアされること"""
        session = self.client.session
        session['csv_preview_data'] = [{'dummy': True}]
        session.save()
        self.client.get(self.url)
        self.assertNotIn('csv_preview_data', self.client.session)

    def test_post_valid_csv_shows_preview(self):
        """正常系: 有効な CSV をアップロード -> プレビューが表示されること"""
        csv_file = _make_csv('new@example.com,新ユーザー,user,営業部')
        response = self.client.post(self.url, {'csv_file': csv_file})
        self.assertEqual(response.status_code, 200)
        self.assertIn('preview_rows', response.context)

    def test_post_valid_csv_has_valid_row(self):
        """正常系: 有効行は is_valid=True でプレビューに含まれること"""
        csv_file = _make_csv('new@example.com,新ユーザー,user,営業部')
        response = self.client.post(self.url, {'csv_file': csv_file})
        preview = response.context['preview_rows']
        self.assertEqual(len(preview), 1)
        self.assertTrue(preview[0]['is_valid'])

    def test_post_saves_preview_to_session(self):
        """正常系: アップロード後にプレビューデータがセッションに保存されること"""
        csv_file = _make_csv('new@example.com,新ユーザー,user,')
        self.client.post(self.url, {'csv_file': csv_file})
        self.assertIn('csv_preview_data', self.client.session)

    def test_post_valid_count_and_error_count(self):
        """正常系: valid_count と error_count がコンテキストに含まれること"""
        csv_file = _make_csv(
            'ok@example.com,有効ユーザー,user,',
            ',名前なし,user,',
        )
        response = self.client.post(self.url, {'csv_file': csv_file})
        self.assertEqual(response.context['valid_count'], 1)
        self.assertEqual(response.context['error_count'], 1)

    # ------------------------------------------------------------------ 異常系（プレビュー）

    def test_duplicate_login_id_marks_invalid(self):
        """異常系: CSV に既存の login_id がある行 -> is_valid=False になること"""
        User.objects.create_user(login_id='dup@example.com', name='既存', password='Pass')
        csv_file = _make_csv('dup@example.com,重複ユーザー,user,')
        response = self.client.post(self.url, {'csv_file': csv_file})
        preview = response.context['preview_rows']
        self.assertFalse(preview[0]['is_valid'])

    def test_invalid_role_marks_invalid(self):
        """異常系: role が admin/user 以外 -> is_valid=False になること"""
        csv_file = _make_csv('new@example.com,テスト,manager,')
        response = self.client.post(self.url, {'csv_file': csv_file})
        preview = response.context['preview_rows']
        self.assertFalse(preview[0]['is_valid'])

    def test_missing_required_field_marks_invalid(self):
        """異常系: login_id または name が空 -> is_valid=False になること"""
        csv_file = _make_csv(',名前なし,user,')
        response = self.client.post(self.url, {'csv_file': csv_file})
        preview = response.context['preview_rows']
        self.assertFalse(preview[0]['is_valid'])

    def test_non_csv_file_rejected(self):
        """異常系: .txt ファイルをアップロード -> フォームエラーになること"""
        txt_file = SimpleUploadedFile('users.txt', b'hello', content_type='text/plain')
        response = self.client.post(self.url, {'csv_file': txt_file})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーでアクセス -> 403 が返ること"""
        User.objects.create_user(login_id='user@example.com', name='一般', password='Pass123', role='user')
        self.client.login(username='user@example.com', password='Pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)


class TestF17CSVImportExecuteView(TestCase):
    """F-17 CSVインポート（実行）のテスト"""

    def setUp(self):
        self.url = reverse('csv_import_execute')
        self.admin = User.objects.create_user(
            login_id='admin@example.com',
            name='管理者',
            password='AdminPass123',
            role='admin',
        )
        self.client.login(username='admin@example.com', password='AdminPass123')

    def _set_session_preview(self, rows):
        session = self.client.session
        session['csv_preview_data'] = rows
        session.save()

    # ------------------------------------------------------------------ 正常系

    def test_execute_creates_valid_users(self):
        """正常系: 有効行のみユーザーが作成されること"""
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '', 'is_valid': True},
        ])
        self.client.post(self.url)
        self.assertTrue(User.objects.filter(login_id='new@example.com').exists())

    def test_execute_skips_invalid_rows(self):
        """正常系: is_valid=False の行はスキップされること"""
        self._set_session_preview([
            {'login_id': 'ok@example.com',  'name': '有効', 'role': 'user', 'dept_name': '', 'is_valid': True},
            {'login_id': 'bad@example.com', 'name': '無効', 'role': 'user', 'dept_name': '', 'is_valid': False},
        ])
        self.client.post(self.url)
        self.assertTrue(User.objects.filter(login_id='ok@example.com').exists())
        self.assertFalse(User.objects.filter(login_id='bad@example.com').exists())

    def test_execute_sets_initial_password(self):
        """正常系: 作成されたユーザーの初期パスワードが 'Bold1234' であること"""
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '', 'is_valid': True},
        ])
        self.client.post(self.url)
        created = User.objects.get(login_id='new@example.com')
        self.assertTrue(created.check_password('Bold1234'))

    def test_execute_creates_department_if_not_exists(self):
        """正常系: dept_name が存在しない場合は Department が自動作成されること"""
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '新規部署', 'is_valid': True},
        ])
        self.client.post(self.url)
        self.assertTrue(Department.objects.filter(name='新規部署').exists())

    def test_execute_uses_existing_department(self):
        """正常系: 既存の Department がある場合は再利用されること"""
        dept = Department.objects.create(name='既存部署')
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '既存部署', 'is_valid': True},
        ])
        self.client.post(self.url)
        self.assertEqual(Department.objects.filter(name='既存部署').count(), 1)

    def test_execute_redirects_to_user_list(self):
        """正常系: インポート成功後 -> ユーザー一覧へリダイレクトされること"""
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '', 'is_valid': True},
        ])
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('user_admin_list'))

    def test_execute_clears_session(self):
        """正常系: インポート成功後にセッションの csv_preview_data がクリアされること"""
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '', 'is_valid': True},
        ])
        self.client.post(self.url)
        self.assertNotIn('csv_preview_data', self.client.session)

    def test_execute_shows_success_message(self):
        """正常系: インポート成功後に成功メッセージが設定されること"""
        self._set_session_preview([
            {'login_id': 'new@example.com', 'name': '新ユーザー', 'role': 'user', 'dept_name': '', 'is_valid': True},
        ])
        response = self.client.post(self.url, follow=True)
        msgs = [str(m) for m in get_messages(response.wsgi_request)]
        self.assertTrue(any('インポート' in m for m in msgs))

    # ------------------------------------------------------------------ 異常系

    def test_execute_without_session_redirects_to_import(self):
        """異常系: セッションなしで実行 -> csv_import へリダイレクトされること"""
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('csv_import'))

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーで実行 -> 403 が返ること"""
        User.objects.create_user(login_id='user@example.com', name='一般', password='Pass123', role='user')
        self.client.login(username='user@example.com', password='Pass123')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
