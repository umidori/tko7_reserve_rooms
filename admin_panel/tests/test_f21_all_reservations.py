"""
F-21: 全予約一覧・管理 (AllReservationListView) の単体テスト
対象ビュー : admin_panel.views.AllReservationListView
URL name  : all_reservation_list  ->  /admin-panel/reservations/

仕様:
  - 管理者のみアクセス可
  - 全予約を開始日時の降順で表示
  - フィルター: date_from / date_to / room / user（氏名部分一致）
  - コンテキスト: form / rooms / total_count / date_from / date_to / now
  - 非管理者 -> 403  /  未認証 -> ログインへリダイレクト
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF21AllReservationList(TestCase):
    """F-21 全予約一覧・管理機能のテスト"""

    def setUp(self):
        self.url = reverse('all_reservation_list')
        self.admin = User.objects.create_user(
            login_id='admin@example.com',
            name='管理者',
            password='AdminPass123',
            role='admin',
        )
        self.user_a = User.objects.create_user(
            login_id='usera@example.com',
            name='山田太郎',
            password='Pass123',
            role='user',
        )
        self.user_b = User.objects.create_user(
            login_id='userb@example.com',
            name='鈴木花子',
            password='Pass123',
            role='user',
        )
        self.room_a = Room.objects.create(name='会議室A', capacity=10, is_active=True)
        self.room_b = Room.objects.create(name='会議室B', capacity=5, is_active=True)

        now = timezone.now()
        # 明日の予約（user_a / room_a）
        self.rsv_future = Reservation.objects.create(
            room=self.room_a,
            user=self.user_a,
            reserved_by='山田太郎',
            title='未来の会議',
            start_at=now + timedelta(days=1),
            end_at=now + timedelta(days=1, hours=1),
        )
        # 昨日の予約（user_b / room_b）
        self.rsv_past = Reservation.objects.create(
            room=self.room_b,
            user=self.user_b,
            reserved_by='鈴木花子',
            title='過去の会議',
            start_at=now - timedelta(days=1),
            end_at=now - timedelta(days=1) + timedelta(hours=1),
        )

        self.client.login(username='admin@example.com', password='AdminPass123')

    # ------------------------------------------------------------------ 正常系

    def test_all_reservations_returns_200(self):
        """正常系: 管理者でアクセス -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_all_reservations_shows_all(self):
        """正常系: フィルターなし -> 全予約がコンテキストに含まれること"""
        response = self.client.get(self.url)
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertIn(self.rsv_past, reservations)

    def test_all_reservations_sorted_descending(self):
        """正常系: 予約が開始日時の降順でソートされること"""
        response = self.client.get(self.url)
        start_times = [r.start_at for r in response.context['reservations']]
        self.assertEqual(start_times, sorted(start_times, reverse=True))

    def test_context_has_rooms(self):
        """正常系: コンテキストに rooms が含まれること"""
        response = self.client.get(self.url)
        self.assertIn('rooms', response.context)

    def test_context_has_total_count(self):
        """正常系: コンテキストに total_count が含まれること"""
        response = self.client.get(self.url)
        self.assertIn('total_count', response.context)

    def test_context_has_form(self):
        """正常系: コンテキストに form が含まれること"""
        response = self.client.get(self.url)
        self.assertIn('form', response.context)

    def test_context_has_now(self):
        """正常系: コンテキストに now が含まれること"""
        response = self.client.get(self.url)
        self.assertIn('now', response.context)

    # ------------------------------------------------------------------ フィルター（正常系）

    def test_filter_by_date_from(self):
        """正常系: date_from 指定 -> 指定日以降の予約のみ表示されること"""
        today_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'date_from': today_str})
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertNotIn(self.rsv_past, reservations)

    def test_filter_by_date_to(self):
        """正常系: date_to 指定 -> 指定日以前の予約のみ表示されること"""
        today_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d')
        response = self.client.get(self.url, {'date_to': today_str})
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_past, reservations)
        self.assertNotIn(self.rsv_future, reservations)

    def test_filter_by_room(self):
        """正常系: room 指定 -> 指定会議室の予約のみ表示されること"""
        response = self.client.get(self.url, {'room': self.room_a.id})
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertNotIn(self.rsv_past, reservations)

    def test_filter_by_user_name(self):
        """正常系: user（氏名部分一致）指定 -> 該当ユーザーの予約のみ表示されること"""
        response = self.client.get(self.url, {'user': '山田'})
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertNotIn(self.rsv_past, reservations)

    def test_filter_combined(self):
        """正常系: date_from + room の AND フィルター -> 両条件を満たす予約のみ表示されること"""
        today_str = timezone.localtime(timezone.now()).strftime('%Y-%m-%d')
        response = self.client.get(self.url, {
            'date_from': today_str,
            'room':      self.room_a.id,
        })
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertNotIn(self.rsv_past, reservations)

    def test_filter_no_match_returns_empty(self):
        """正常系: 条件に一致する予約が0件 -> 0件になること"""
        response = self.client.get(self.url, {'user': '存在しない名前'})
        self.assertEqual(response.context['reservations'].count(), 0)

    def test_invalid_date_from_ignored(self):
        """正常系: date_from に不正値 -> フィルターなしで全件表示されること"""
        response = self.client.get(self.url, {'date_from': 'not-a-date'})
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertIn(self.rsv_past, reservations)

    def test_invalid_room_id_ignored(self):
        """正常系: room に不正値 -> フィルターなしで全件表示されること"""
        response = self.client.get(self.url, {'room': 'abc'})
        reservations = list(response.context['reservations'])
        self.assertIn(self.rsv_future, reservations)
        self.assertIn(self.rsv_past, reservations)

    # ------------------------------------------------------------------ 異常系

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーでアクセス -> 403 が返ること"""
        self.client.login(username='usera@example.com', password='Pass123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '/accounts/login/?next={}'.format(self.url),
        )
