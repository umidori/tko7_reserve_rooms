"""
F-07: 会議室一覧表示 (RoomListView) の単体テスト
対象ビュー : rooms.views.RoomListView
URL name  : rooms:room_list  ->  /rooms/

仕様:
  - 全会議室を一覧表示（is_active=False も「利用停止中」バッジを付けて表示）
  - 室名・収容人数・設備・建物/階数・利用可否を表示
  - 室名リンクは当該会議室のカレンダーへ遷移
"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from reservations.models import Building, Facility, Room


class TestF07RoomList(TestCase):
    """F-07 会議室一覧表示機能のテスト"""

    def setUp(self):
        self.url = reverse('rooms:room_list')
        self.login_url = '/accounts/login/'

        self.user = User.objects.create_user(
            login_id='test@example.com',
            name='テストユーザー',
            password='TestPass123',
        )
        self.building = Building.objects.create(name='本館')
        self.facility = Facility.objects.create(name='プロジェクター')

        # 利用可の会議室（建物・設備・階数あり）
        self.active_room = Room.objects.create(
            name='会議室A',
            capacity=10,
            building=self.building,
            floor=2,
            is_active=True,
        )
        self.active_room.facilities.add(self.facility)

        # 利用停止中の会議室（建物・設備・階数なし）
        self.inactive_room = Room.objects.create(
            name='会議室B',
            capacity=5,
            is_active=False,
        )

        self.client.login(username='test@example.com', password='TestPass123')

    # ------------------------------------------------------------------ 正常系

    def test_room_list_returns_200(self):
        """正常系: /rooms/ にアクセス -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_room_list_shows_all_rooms_including_inactive(self):
        """正常系: フィルターなし -> 利用停止中を含む全会議室がコンテキストに含まれること"""
        response = self.client.get(self.url)
        rooms = list(response.context['rooms'])
        self.assertIn(self.active_room, rooms)
        self.assertIn(self.inactive_room, rooms)

    def test_room_list_shows_room_name(self):
        """正常系: 会議室名が一覧に表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, '会議室A')
        self.assertContains(response, '会議室B')

    def test_room_list_shows_capacity(self):
        """正常系: 収容人数が「○名」形式で一覧に表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, '10名')
        self.assertContains(response, '5名')

    def test_room_list_shows_facility(self):
        """正常系: 設備名が一覧に表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, 'プロジェクター')

    def test_room_list_shows_building_and_floor(self):
        """正常系: 建物名と階数が一覧に表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, '本館')
        self.assertContains(response, '2階')

    def test_active_room_shows_active_badge(self):
        """正常系: is_active=True の会議室に「利用可」バッジが表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, '利用可')

    def test_inactive_room_shows_stopped_badge(self):
        """正常系: is_active=False の会議室に「利用停止中」バッジが表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, '利用停止中')

    def test_room_name_links_to_calendar_with_room_id(self):
        """正常系: 室名リンクが当該会議室のカレンダーURL を持つこと"""
        response = self.client.get(self.url)
        # href 属性内の & は HTML 的に &amp; とエスケープされて出力される
        expected_url = '/calendar/?filter=all&amp;room_id={}'.format(self.active_room.id)
        self.assertContains(response, expected_url)

    def test_room_list_sorted_by_name(self):
        """正常系: 会議室が室名の昇順でソートされること"""
        response = self.client.get(self.url)
        names = [r.name for r in response.context['rooms']]
        self.assertEqual(names, sorted(names))

    def test_room_with_no_facility_shows_dash(self):
        """正常系: 設備なし会議室の設備列に「―」が表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, '\u2015')

    def test_room_list_empty_shows_no_results_message(self):
        """正常系: 会議室が0件 -> 「条件に一致する会議室が見つかりませんでした」が表示されること"""
        Room.objects.all().delete()
        response = self.client.get(self.url)
        self.assertContains(response, '条件に一致する会議室が見つかりませんでした')

    def test_search_form_in_context(self):
        """正常系: 検索フォームオブジェクトがコンテキストに含まれること"""
        response = self.client.get(self.url)
        self.assertIn('form', response.context)

    # ------------------------------------------------------------------ 異常系

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            '{}?next={}'.format(self.login_url, self.url),
        )
