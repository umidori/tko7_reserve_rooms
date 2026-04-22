from django.urls import path
from .views import (
    RoomAdminListView,
    RoomCreateView,
    RoomUpdateView,
    RoomDeleteView,
    RoomToggleActiveView,
)
from accounts.views import (
    UserListView,
    UserCreateView,
    UserUpdateView,
    UserToggleActiveView,
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

    # F-14〜F-16：ユーザー管理
    path('users/',
         UserListView.as_view(),          name='user_admin_list'),
    path('users/create/',
         UserCreateView.as_view(),        name='user_create'),
    path('users/<int:pk>/edit/',
         UserUpdateView.as_view(),        name='user_edit'),
    path('users/<int:pk>/toggle-active/',
         UserToggleActiveView.as_view(),  name='user_toggle_active'),
]
