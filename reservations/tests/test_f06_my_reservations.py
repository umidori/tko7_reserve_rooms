"""
F-06: 自分の予約一覧表示 (MyReservationListView) の単体テスト
対象ビュー : reservations.views.MyReservationListView
URL name  : my_reservations  →  /reservations/my/
"""
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from reservations.models import Reservation, Room


class TestF06MyReservationListView(TestCase):
    """F-06 自分の予約一覧表示機能のテスト"""

    def setUp(self):
        self.url = reverse('my_reservations')
        self.login_url = '/accounts/login/'
        self.now = timezone.now()

        # メインユーザー
        self.user = User.objects.create_user(
            login_id='test@example.com',
            name='テストユーザー',
            password='TestPass123',
        )
        # 他のユーザー
        self.other_user = User.objects.create_user(
            login_id='other@example.com',
            name='他のユーザー',
            password='TestPass123',
        )
        self.room = Room.objects.create(name='会議室A', capacity=10, is_active=True)

        # 今後の予約（1日後・キャンセルなし）
        self.upcoming_rsv = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by='テストユーザー',
            title='今後の会議',
            start_at=self.now + timedelta(days=1),
            end_at=self.now + timedelta(days=1, hours=1),
            is_cancelled=False,
        )
        # 過去の予約（1日前・キャンセルなし）
        self.past_rsv = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by='テストユーザー',
            title='過去の会議',
            start_at=self.now - timedelta(days=1),
            end_at=self.now - timedelta(days=1) + timedelta(hours=1),
            is_cancelled=False,
        )
        # 過去のキャンセル済み予約（2日前）
        self.past_cancelled_rsv = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by='テストユーザー',
            title='過去のキャンセル済み会議',
            start_at=self.now - timedelta(days=2),
            end_at=self.now - timedelta(days=2) + timedelta(hours=1),
            is_cancelled=True,
        )
        # 今後のキャンセル済み予約（3日後）
        self.future_cancelled_rsv = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by='テストユーザー',
            title='今後のキャンセル済み会議',
            start_at=self.now + timedelta(days=3),
            end_at=self.now + timedelta(days=3, hours=1),
            is_cancelled=True,
        )
        # 他のユーザーの今後の予約
        self.other_rsv = Reservation.objects.create(
            room=self.room,
            user=self.other_user,
            reserved_by='他のユーザー',
            title='他人の会議',
            start_at=self.now + timedelta(days=4),
            end_at=self.now + timedelta(days=4, hours=1),
            is_cancelled=False,
        )

        self.client.login(username='test@example.com', password='TestPass123')

    # ──────────────────────────────────────────────
    # 正常系
    # ──────────────────────────────────────────────

    def test_upcoming_tab_is_default(self):
        """正常系: ?tab 指定なしでアクセス → 「今後の予約」タブがデフォルト表示されること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['active_tab'], 'upcoming')

    def test_upcoming_tab_shows_future_non_cancelled_reservations(self):
        """正常系: 今後のタブ → 現在以降のキャンセルされていない自分の予約のみ表示されること"""
        response = self.client.get(self.url, {'tab': 'upcoming'})
        reservations = list(response.context['reservations'])
        self.assertIn(self.upcoming_rsv, reservations)
        self.assertNotIn(self.past_rsv, reservations)
        self.assertNotIn(self.future_cancelled_rsv, reservations)

    def test_upcoming_tab_sorted_ascending(self):
        """正常系: 今後のタブ → 開始日時の昇順でソートされること"""
        upcoming2 = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by='テストユーザー',
            title='今後の会議2',
            start_at=self.now + timedelta(days=5),
            end_at=self.now + timedelta(days=5, hours=1),
            is_cancelled=False,
        )
        response = self.client.get(self.url, {'tab': 'upcoming'})
        reservations = list(response.context['reservations'])
        start_times = [r.start_at for r in reservations]
        self.assertEqual(start_times, sorted(start_times))

    def test_past_tab_shows_past_reservations_including_cancelled(self):
        """正常系: 過去のタブ → 現在より前の自分の予約（キャンセル済みを含む）が表示されること"""
        response = self.client.get(self.url, {'tab': 'past'})
        reservations = list(response.context['reservations'])
        self.assertIn(self.past_rsv, reservations)
        self.assertIn(self.past_cancelled_rsv, reservations)
        self.assertNotIn(self.upcoming_rsv, reservations)

    def test_past_tab_sorted_descending(self):
        """正常系: 過去のタブ → 開始日時の降順でソートされること"""
        past2 = Reservation.objects.create(
            room=self.room,
            user=self.user,
            reserved_by='テストユーザー',
            title='過去の会議2',
            start_at=self.now - timedelta(days=3),
            end_at=self.now - timedelta(days=3) + timedelta(hours=1),
            is_cancelled=False,
        )
        response = self.client.get(self.url, {'tab': 'past'})
        reservations = list(response.context['reservations'])
        start_times = [r.start_at for r in reservations]
        self.assertEqual(start_times, sorted(start_times, reverse=True))

    def test_other_users_reservations_not_shown_in_upcoming(self):
        """正常系: 他のユーザーの予約は今後のタブに表示されないこと"""
        response = self.client.get(self.url, {'tab': 'upcoming'})
        reservations = list(response.context['reservations'])
        self.assertNotIn(self.other_rsv, reservations)

    def test_upcoming_count_in_context(self):
        """正常系: upcoming_count にキャンセルされていない今後の予約件数が格納されること"""
        response = self.client.get(self.url, {'tab': 'upcoming'})
        self.assertEqual(response.context['upcoming_count'], 1)

    def test_past_count_in_context(self):
        """正常系: past_count に過去の予約件数（キャンセル含む）が格納されること"""
        response = self.client.get(self.url, {'tab': 'past'})
        # past_rsv（1件）＋ past_cancelled_rsv（1件）= 2件
        self.assertEqual(response.context['past_count'], 2)

    def test_empty_upcoming_shows_no_reservation_message(self):
        """正常系: 今後の予約が0件 → 「今後の予約はありません」メッセージが表示されること"""
        # 今後の予約をキャンセル
        self.upcoming_rsv.is_cancelled = True
        self.upcoming_rsv.save()
        response = self.client.get(self.url, {'tab': 'upcoming'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '今後の予約はありません')

    def test_empty_past_shows_no_reservation_message(self):
        """正常系: 過去の予約が0件 → 「過去の予約はありません」メッセージが表示されること"""
        # 別ユーザーでログイン（過去の予約なし）
        new_user = User.objects.create_user(
            login_id='new@example.com',
            name='新規ユーザー',
            password='TestPass123',
        )
        self.client.login(username='new@example.com', password='TestPass123')
        response = self.client.get(self.url, {'tab': 'past'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '過去の予約はありません')

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス → ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            f'{self.login_url}?next={self.url}',
        )
