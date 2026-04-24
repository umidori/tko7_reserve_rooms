"""
F-08: 会議室絞り込み検索 (RoomListView) の単体テスト
対象ビュー : rooms.views.RoomListView
URL name  : rooms:room_list  →  /rooms/

仕様:
  - capacity  : rooms.capacity >= 指定値（1以上の整数。不正値はフィルターなし）
  - facility  : 指定した全設備を持つ会議室のみ表示（AND 条件・複数選択可）
  - building  : rooms.building_id = 指定値
  - floor     : rooms.floor = 指定値
  - 複数条件は AND 結合
"""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from reservations.models import Building, Facility, Room


class TestF08RoomSearch(TestCase):
    """F-08 会議室絞り込み検索機能のテスト"""

    def setUp(self):
        self.url = reverse('rooms:room_list')

        self.user = User.objects.create_user(
            login_id='test@example.com',
            name='テストユーザー',
            password='TestPass123',
        )

        # 建物
        self.building_main = Building.objects.create(name='本館')
        self.building_annex = Building.objects.create(name='別館')

        # 設備
        self.projector = Facility.objects.create(name='プロジェクター')
        self.whiteboard = Facility.objects.create(name='ホワイトボード')

        # 大会議室：20名・本館3階・プロジェクター＋ホワイトボード
        self.room_large = Room.objects.create(
            name='大会議室',
            capacity=20,
            building=self.building_main,
            floor=3,
            is_active=True,
        )
        self.room_large.facilities.add(self.projector, self.whiteboard)

        # 中会議室：10名・本館2階・プロジェクターのみ
        self.room_medium = Room.objects.create(
            name='中会議室',
            capacity=10,
            building=self.building_main,
            floor=2,
            is_active=True,
        )
        self.room_medium.facilities.add(self.projector)

        # 小会議室：4名・別館1階・設備なし
        self.room_small = Room.objects.create(
            name='小会議室',
            capacity=4,
            building=self.building_annex,
            floor=1,
            is_active=True,
        )

        self.client.login(username='test@example.com', password='TestPass123')

    # ──────────────────────────────────────────────
    # 正常系 ── capacity フィルター
    # ──────────────────────────────────────────────

    def test_filter_capacity_includes_equal_value(self):
        """正常系: capacity=10 → 収容人数ちょうど10名の会議室も含まれること"""
        response = self.client.get(self.url, {'capacity': 10})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_medium, rooms)   # 10名 ✓

    def test_filter_capacity_excludes_smaller_rooms(self):
        """正常系: capacity=10 → 収容人数10名未満の会議室が除外されること"""
        response = self.client.get(self.url, {'capacity': 10})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)    # 20名 ✓
        self.assertIn(self.room_medium, rooms)   # 10名 ✓
        self.assertNotIn(self.room_small, rooms) # 4名 ✗

    def test_filter_capacity_strict(self):
        """正常系: capacity=15 → 15名以上の会議室のみ表示されること"""
        response = self.client.get(self.url, {'capacity': 15})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertNotIn(self.room_medium, rooms)
        self.assertNotIn(self.room_small, rooms)

    # ──────────────────────────────────────────────
    # 正常系 ── facility フィルター
    # ──────────────────────────────────────────────

    def test_filter_single_facility(self):
        """正常系: 設備1つ指定 → その設備を持つ会議室のみ表示されること"""
        response = self.client.get(self.url, {'facility': self.projector.id})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertIn(self.room_medium, rooms)
        self.assertNotIn(self.room_small, rooms)

    def test_filter_multiple_facilities_is_and_condition(self):
        """正常系: 設備を複数選択 → 全設備を持つ会議室のみ表示（AND 条件）されること"""
        response = self.client.get(self.url, {
            'facility': [self.projector.id, self.whiteboard.id],
        })
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)      # 両方あり ✓
        self.assertNotIn(self.room_medium, rooms)  # whiteboard なし ✗
        self.assertNotIn(self.room_small, rooms)   # 両方なし ✗

    def test_filter_facility_with_no_match_returns_empty(self):
        """正常系: 保有会議室が0件の設備で検索 → 0件になること"""
        whiteboard_only = Facility.objects.create(name='テレビ会議システム')
        response = self.client.get(self.url, {'facility': whiteboard_only.id})
        rooms = list(response.context['rooms'])
        self.assertEqual(len(rooms), 0)

    # ──────────────────────────────────────────────
    # 正常系 ── building フィルター
    # ──────────────────────────────────────────────

    def test_filter_by_building(self):
        """正常系: building=本館 → 本館の会議室のみ表示されること"""
        response = self.client.get(self.url, {'building': self.building_main.id})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertIn(self.room_medium, rooms)
        self.assertNotIn(self.room_small, rooms)

    def test_filter_by_building_annex(self):
        """正常系: building=別館 → 別館の会議室のみ表示されること"""
        response = self.client.get(self.url, {'building': self.building_annex.id})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_small, rooms)
        self.assertNotIn(self.room_large, rooms)
        self.assertNotIn(self.room_medium, rooms)

    # ──────────────────────────────────────────────
    # 正常系 ── floor フィルター
    # ──────────────────────────────────────────────

    def test_filter_by_floor(self):
        """正常系: floor=3 → 3階の会議室のみ表示されること"""
        response = self.client.get(self.url, {'floor': 3})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertNotIn(self.room_medium, rooms)
        self.assertNotIn(self.room_small, rooms)

    # ──────────────────────────────────────────────
    # 正常系 ── 複合フィルター（AND 条件）
    # ──────────────────────────────────────────────

    def test_filter_combined_capacity_and_facility(self):
        """正常系: capacity + facility の AND 絞り込み → 両条件を満たす会議室のみ表示されること"""
        response = self.client.get(self.url, {
            'capacity': 10,
            'facility': self.whiteboard.id,
        })
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)      # 20名・whiteboard あり ✓
        self.assertNotIn(self.room_medium, rooms)  # whiteboard なし ✗
        self.assertNotIn(self.room_small, rooms)   # 4名・whiteboard なし ✗

    def test_filter_combined_building_and_floor(self):
        """正常系: building + floor の AND 絞り込み → 両条件を満たす会議室のみ表示されること"""
        response = self.client.get(self.url, {
            'building': self.building_main.id,
            'floor': 2,
        })
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_medium, rooms)     # 本館2階 ✓
        self.assertNotIn(self.room_large, rooms)   # 本館3階 ✗
        self.assertNotIn(self.room_small, rooms)   # 別館1階 ✗

    # ──────────────────────────────────────────────
    # 正常系 ── is_filtered コンテキスト
    # ──────────────────────────────────────────────

    def test_is_filtered_true_when_params_provided(self):
        """正常系: 検索条件あり → is_filtered=True がコンテキストに設定されること"""
        response = self.client.get(self.url, {'capacity': 10})
        self.assertTrue(response.context['is_filtered'])

    def test_is_filtered_false_when_no_params(self):
        """正常系: 検索条件なし → is_filtered=False がコンテキストに設定されること"""
        response = self.client.get(self.url)
        self.assertFalse(response.context['is_filtered'])

    def test_filter_no_match_shows_empty_message(self):
        """正常系: 条件に一致する会議室が0件 → 「条件に一致する会議室が見つかりませんでした」が表示されること"""
        response = self.client.get(self.url, {'capacity': 9999})
        self.assertContains(response, '条件に一致する会議室が見つかりませんでした')

    # ──────────────────────────────────────────────
    # 異常系
    # ──────────────────────────────────────────────

    def test_invalid_capacity_string_shows_all_rooms(self):
        """異常系: capacity='abc'（文字列）→ フィルタリングなしで全件表示されること"""
        response = self.client.get(self.url, {'capacity': 'abc'})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertIn(self.room_medium, rooms)
        self.assertIn(self.room_small, rooms)

    def test_invalid_capacity_zero_shows_all_rooms(self):
        """異常系: capacity=0（min_value=1 未満）→ フィルタリングなしで全件表示されること"""
        response = self.client.get(self.url, {'capacity': 0})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertIn(self.room_medium, rooms)
        self.assertIn(self.room_small, rooms)

    def test_invalid_floor_string_shows_all_rooms(self):
        """異常系: floor='abc'（文字列）→ フィルタリングなしで全件表示されること"""
        response = self.client.get(self.url, {'floor': 'abc'})
        rooms = list(response.context['rooms'])
        self.assertIn(self.room_large, rooms)
        self.assertIn(self.room_medium, rooms)
        self.assertIn(self.room_small, rooms)
