from django.urls import path
from .views import (
    home,
    CalendarView,
    ReservationCreateView,
    MyReservationListView,
)

urlpatterns = [
    path('', CalendarView.as_view(), name='home'),

    # F-04: calendar
    path('calendar/', CalendarView.as_view(), name='calendar'),

    # F-05: reservation create
    path('reservations/create/', ReservationCreateView.as_view(), name='reservation_create'),

    # F-06: my reservations list  (/reservations/my/?tab=upcoming or ?tab=past)
    path('reservations/my/', MyReservationListView.as_view(), name='my_reservations'),
]
