"""
F-18: 会議室マスタ管理 (RoomAdminListView / RoomCreateView / RoomUpdateView) の単体テスト
対象ビュー : admin_panel.views.RoomAdminListView / RoomCreateView / RoomUpdateView
URL name  : room_admin_list  ->  /admin-panel/rooms/
           room_create       ->  /admin-panel/rooms/create/
           room_edit         ->  /admin-panel/rooms/<pk>/edit/

仕様:
  - 管理者のみアクセス可（非管理者 -> 403 / 未認証 -> ログインへリダイレクト）
  - 一覧: 全会議室を表示（建物・設備・所属別表示設定を含む）
  - 新規: 室名・収容人数を必須登録、設備/所属/建物/階数はオプション
  - 新規: 室名重複 -> バリデーションエラー
  - 編集: 室名・収容人数・設備等を更新
  - 成功後 -> 会議室一覧へリダイレクト
"""

from django.test import TestCase
from django.urls import reverse

from accounts.models import Department, User
from reservations.models import Building, Facility, Room, RoomFacility


class TestF18RoomAdminList(TestCase):
    """F-18 会議室一覧（管理画面）のテスト"""

    def setUp(self):
        self.url = reverse("room_admin_list")
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.client.login(username="admin@example.com", password="AdminPass123")

    def test_room_admin_list_returns_200(self):
        """正常系: 管理者でアクセス -> 200 OK が返ること"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_room_admin_list_shows_rooms(self):
        """正常系: 会議室がコンテキストに含まれること"""
        response = self.client.get(self.url)
        self.assertIn(self.room, response.context["rooms"])

    def test_room_admin_list_shows_room_name(self):
        """正常系: 会議室名がページに表示されること"""
        response = self.client.get(self.url)
        self.assertContains(response, "会議室A")

    def test_room_admin_list_context_has_buildings(self):
        """正常系: コンテキストに buildings が含まれること"""
        response = self.client.get(self.url)
        self.assertIn("buildings", response.context)

    def test_room_admin_list_context_has_facilities(self):
        """正常系: コンテキストに facilities が含まれること"""
        response = self.client.get(self.url)
        self.assertIn("facilities", response.context)

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーでアクセス -> 403 が返ること"""
        User.objects.create_user(
            login_id="user@example.com", name="一般", password="Pass123", role="user"
        )
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_redirects_to_login(self):
        """異常系: 未ログイン状態でアクセス -> ログイン画面へリダイレクトされること"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(
            response,
            "/accounts/login/?next={}".format(self.url),
        )


class TestF18RoomCreate(TestCase):
    """F-18 会議室新規登録のテスト"""

    def setUp(self):
        self.url = reverse("room_create")
        self.list_url = reverse("room_admin_list")
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.client.login(username="admin@example.com", password="AdminPass123")

    def _valid_post(self, **overrides):
        data = {
            "name": "新会議室",
            "capacity": 10,
            "facilities": [],
            "departments": [],
            "building": "",
            "floor": "",
        }
        data.update(overrides)
        return data

    def test_create_room_success(self):
        """正常系: 有効な入力で POST -> 会議室が1件作成されること"""
        self.client.post(self.url, self._valid_post())
        self.assertTrue(Room.objects.filter(name="新会議室").exists())

    def test_create_room_redirects_to_list(self):
        """正常系: 作成成功後 -> 会議室一覧へリダイレクトされること"""
        response = self.client.post(self.url, self._valid_post())
        self.assertRedirects(response, self.list_url)

    def test_create_room_with_facility(self):
        """正常系: 設備付きで作成 -> RoomFacility が登録されること"""
        facility = Facility.objects.create(name="プロジェクター")
        self.client.post(self.url, self._valid_post(facilities=[facility.pk]))
        room = Room.objects.get(name="新会議室")
        self.assertIn(facility, room.facilities.all())

    def test_create_room_with_building_and_floor(self):
        """正常系: 建物・階数付きで作成 -> 正しく保存されること"""
        building = Building.objects.create(name="本館")
        self.client.post(self.url, self._valid_post(building=building.pk, floor=3))
        room = Room.objects.get(name="新会議室")
        self.assertEqual(room.building, building)
        self.assertEqual(room.floor, 3)

    def test_create_room_with_department(self):
        """正常系: 所属別表示設定付きで作成 -> DepartmentRoom が登録されること"""
        dept = Department.objects.create(name="営業部")
        self.client.post(self.url, self._valid_post(departments=[dept.pk]))
        room = Room.objects.get(name="新会議室")
        self.assertIn(dept, room.departments.all())

    def test_duplicate_room_name_shows_error(self):
        """異常系: 既存の室名 -> バリデーションエラーになり作成されないこと"""
        Room.objects.create(name="既存会議室", capacity=5)
        response = self.client.post(self.url, self._valid_post(name="既存会議室"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Room.objects.filter(name="既存会議室").count(), 1)

    def test_empty_name_shows_error(self):
        """異常系: 室名が空欄 -> バリデーションエラーになること"""
        response = self.client.post(self.url, self._valid_post(name=""))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Room.objects.filter(name="").exists())

    def test_non_admin_gets_403(self):
        """異常系: 一般ユーザーで POST -> 403 が返ること"""
        User.objects.create_user(
            login_id="user@example.com", name="一般", password="Pass123", role="user"
        )
        self.client.login(username="user@example.com", password="Pass123")
        response = self.client.post(self.url, self._valid_post())
        self.assertEqual(response.status_code, 403)


class TestF18RoomUpdate(TestCase):
    """F-18 会議室編集のテスト"""

    def setUp(self):
        self.admin = User.objects.create_user(
            login_id="admin@example.com",
            name="管理者",
            password="AdminPass123",
            role="admin",
        )
        self.room = Room.objects.create(name="会議室A", capacity=10, is_active=True)
        self.url = reverse("room_edit", kwargs={"pk": self.room.pk})
        self.list_url = reverse("room_admin_list")
        self.client.login(username="admin@example.com", password="AdminPass123")

    def _valid_post(self, **overrides):
        data = {
            "name": "更新後会議室",
            "capacity": 20,
            "facilities": [],
            "departments": [],
            "building": "",
            "floor": "",
        }
        data.update(overrides)
        return data

    def test_update_room_name(self):
        """正常系: 室名を変更して保存 -> 室名が更新されること"""
        self.client.post(self.url, self._valid_post(name="更新後会議室"))
        self.room.refresh_from_db()
        self.assertEqual(self.room.name, "更新後会議室")

    def test_update_room_capacity(self):
        """正常系: 収容人数を変更して保存 -> 収容人数が更新されること"""
        self.client.post(self.url, self._valid_post(capacity=20))
        self.room.refresh_from_db()
        self.assertEqual(self.room.capacity, 20)

    def test_update_room_redirects_to_list(self):
        """正常系: 更新成功後 -> 会議室一覧へリダイレクトされること"""
        response = self.client.post(self.url, self._valid_post())
        self.assertRedirects(response, self.list_url)

    def test_update_room_replaces_facilities(self):
        """正常系: 設備を差し替えて保存 -> 新しい設備のみ登録されること"""
        old_facility = Facility.objects.create(name="プロジェクター")
        new_facility = Facility.objects.create(name="ホワイトボード")
        RoomFacility.objects.create(room=self.room, facility=old_facility)
        self.client.post(self.url, self._valid_post(facilities=[new_facility.pk]))
        self.room.refresh_from_db()
        self.assertIn(new_facility, self.room.facilities.all())
        self.assertNotIn(old_facility, self.room.facilities.all())

    def test_nonexistent_room_returns_404(self):
        """異常系: 存在しない pk -> 404 が返ること"""
        url = reverse("room_edit", kwargs={"pk": 9999})
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
