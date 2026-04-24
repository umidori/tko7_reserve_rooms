"""
F-04: 日次カレンダー表示 (CalendarView) の単体テスト
対象ビュー : reservations.views.CalendarView
URL name  : calendar  →  /calendar/
"""
from datetime import date, datetime, timedelta

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User
from reservations.models import DepartmentRoom, Reservation, Room


class TestF04CalendarView(TestCase):
    """F-04 日次カレンダー表示機能のテスト"""

    def setUp(self):
        self.url = reverse('calendar')
        self.login_url = '/accounts/login/'

        # 所属・ユーザーを作成
        self.dept = Department.objects.create(name='開発部')
        self.user = User.objects.create_user(
            login_id='test@example.com',
            name='テストユーザー',
            password='TestPass123',
            department=self.dept,
        )

        # 会議室を2つ作成
        self.room1 = Room.objects.create(name='会議室A', capacity=10, is_active=True)
        self.room2 = Room.objects.create(name='会議室B', capacity=5, is_active=True)

        # room1 だけを開発部に紐づけ
        DepartmentRoom.objects.create(department=self.dept, room=self.room1)

        self.client.login(username='test@example.com', password='TestPass123')

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_calendar_default_shows_today(self):
        """正常系: dateパラメータなしでアクセス → 当日の日付が表示されること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['target_date'], date.today())

    def test_calendar_with_date_param(self):
        """正常系: ?date=YYYY-MM-DD → 指定日のカレンダーが表示されること"""
        response = self.client.get(self.url, {'date': '2026-05-01'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['target_date'], date(2026, 5, 1))

    def test_calendar_prev_date_is_one_day_before(self):
        """正常系: prev_date が target_date の前日であること"""
        response = self.client.get(self.url, {'date': '2026-05-10'})
        self.assertEqual(response.context['prev_date'], date(2026, 5, 9))

    def test_calendar_next_date_is_one_day_after(self):
        """正常系: next_date が target_date の翌日であること"""
        response = self.client.get(self.url, {'date': '2026-05-10'})
        self.assertEqual(response.context['next_date'], date(2026, 5, 11))

    def test_calendar_department_filter_shows_only_dept_rooms(self):
        """正常系: 所属に紐づく会議室がある場合 → 所属の会議室のみ初期表示されること"""
        response = self.client.get(self.url)
        rooms = list(response.context['rooms'])
        self.assertIn(self.room1, rooms)
        self.assertNotIn(self.room2, rooms)

    def test_calendar_filter_all_shows_all_active_rooms(self):
        """正常系: ?filter=all → 全アクティブ会議室が表示されること"""
        response = self.client.get(self.url, {'filter': 'all'})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room1, rooms)
        self.assertIn(self.room2, rooms)

    def test_calendar_user_without_department_shows_all_rooms(self):
        """正常系: 所属なしユーザー → 全アクティブ会議室が初期表示されること"""
        user_no_dept = User.objects.create_user(
            login_id='nodept@example.com',
            name='所属なしユーザー',
            password='TestPass123',
        )
        self.client.login(username='nodept@example.com', password='TestPass123')
        response = self.client.get(self.url)
        rooms = list(response.context['rooms'])
        self.assertIn(self.room1, rooms)
        self.assertIn(self.room2, rooms)

    def test_calendar_inactive_room_excluded_from_all_filter(self):
        """正常系: is_active=False の会議室は ?filter=all でも表示されないこと"""
        inactive_room = Room.objects.create(
            name='会議室C（停止中）', capacity=8, is_active=False
        )
        response = self.client.get(self.url, {'filter': 'all'})
        rooms = list(response.context['rooms'])
        self.assertNotIn(inactive_room, rooms)

    def test_calendar_grid_has_48_slots(self):
        """正常系: グリッドが 00:00〜23:30 の 48 スロットで構成されること"""
        response = self.client.get(self.url)
        grid = response.context['grid']
        self.assertEqual(len(grid), 48)

    def test_calendar_grid_first_slot_is_midnight(self):
        """正常系: グリッドの先頭スロットが 00:00 であること"""
        response = self.client.get(self.url)
        first_slot = response.context['grid'][0]['slot']
        self.assertEqual(first_slot, datetime.strptime('00:00', '%H:%M').time())

    def test_calendar_grid_last_slot_is_2330(self):
        """正常系: グリッドの末尾スロットが 23:30 であること"""
        response = self.client.get(self.url)
        last_slot = response.context['grid'][-1]['slot']
        self.assertEqual(last_slot, datetime.strptime('23:30', '%H:%M').time())

    def test_calendar_departments_in_context(self):
        """正常系: フィルタードロップダウン用に departments がコンテキストに含まれること"""
        response = self.client.get(self.url)
        self.assertIn(self.dept, list(response.context['departments']))

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_calendar_invalid_date_falls_back_to_today(self):
        """異常系: 不正な date パラメータ → 当日にフォールバックすること"""
        response = self.client.get(self.url, {'date': 'invalid-date'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['target_date'], date.today())

    def test_calendar_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス → ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, f'{self.login_url}?next={self.url}')
