from django.urls import path
from .views import (
    home,
    CalendarView,
    ReservationCreateView,
)

urlpatterns = [
    path('', CalendarView.as_view(), name='home'),

    # F-04：日次カレンダー
    # /calendar/?date=YYYY-MM-DD でアクセスする
    path('calendar/', CalendarView.as_view(), name='calendar'),
    path('reservations/create/', ReservationCreateView.as_view(), name='reservation_create'),
]
