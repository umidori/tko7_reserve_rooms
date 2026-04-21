from django.urls import path
from .views import (
    RoomAdminListView,
    RoomCreateView,
    RoomUpdateView,
    RoomDeleteView,
    RoomToggleActiveView,
)

urlpatterns = [
    # F-18〜F-20：会議室マスタ管理
    path('rooms/',
         RoomAdminListView.as_view(),     name='room_admin_list'),
    path('rooms/create/',
         RoomCreateView.as_view(),        name='room_create'),
    path('rooms/<int:pk>/edit/',
         RoomUpdateView.as_view(),        name='room_edit'),
    path('rooms/<int:pk>/delete/',
         RoomDeleteView.as_view(),        name='room_delete'),
    path('rooms/<int:pk>/toggle-active/',
         RoomToggleActiveView.as_view(),  name='room_toggle_active'),
]
