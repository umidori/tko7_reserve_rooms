from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import (
    home,
    RoomAdminListView,
    RoomCreateView,
    RoomUpdateView,
    RoomDeleteView,
    RoomToggleActiveView,
)

urlpatterns = [
    path('', login_required(home), name='home'),

    # ── 会議室マスタ管理（F-18〜F-20）──
    path('admin-panel/rooms/',
         RoomAdminListView.as_view(),     name='room_admin_list'),
    path('admin-panel/rooms/create/',
         RoomCreateView.as_view(),        name='room_create'),
    path('admin-panel/rooms/<int:pk>/edit/',
         RoomUpdateView.as_view(),        name='room_edit'),
    path('admin-panel/rooms/<int:pk>/delete/',
         RoomDeleteView.as_view(),        name='room_delete'),
    path('admin-panel/rooms/<int:pk>/toggle-active/',
         RoomToggleActiveView.as_view(),  name='room_toggle_active'),
]
