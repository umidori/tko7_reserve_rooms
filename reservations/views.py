from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.views.generic import TemplateView, CreateView, ListView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date, datetime, timedelta
from django.utils import timezone
from django.utils.timezone import localtime
from django.urls import reverse

from .models import Room, Reservation
from .forms import ReservationForm
from accounts.models import Department
from django.views.generic import DetailView


def home(request):
    return HttpResponse("meeting room reservation system")


# F-04
class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = "reservations/calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        date_str = self.request.GET.get("date")
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            target_date = date.today()

        departments = Department.objects.all().order_by("name")

        user = self.request.user
        default_filter = str(user.department_id) if user.department_id else "all"
        filter_value = self.request.GET.get("filter", default_filter)

        rooms = Room.objects.none()

        room_id_str = self.request.GET.get("room_id")
        room_id = None
        if room_id_str:
            try:
                room_id = int(room_id_str)
            except (ValueError, TypeError):
                room_id = None

        if room_id:
            rooms = Room.objects.filter(id=room_id, is_active=True)
            if not rooms.exists():
                rooms = Room.objects.filter(is_active=True).order_by("name")
            filter_value = "all"
        else:
            if filter_value != "all":
                try:
                    dept_id = int(filter_value)
                    rooms = Room.objects.filter(
                        is_active=True,
                        departmentroom__department_id=dept_id,
                    ).order_by("name")
                except (ValueError, TypeError):
                    filter_value = "all"

            if filter_value == "all" or not rooms.exists():
                rooms = Room.objects.filter(is_active=True).order_by("name")
                filter_value = "all"

        slots = []
        current = datetime.combine(target_date, datetime.min.time())
        end_of_day = current.replace(hour=23, minute=30)
        while current <= end_of_day:
            slots.append(current.time())
            current += timedelta(minutes=30)

        reservations = Reservation.objects.filter(
            start_at__date=target_date,
            is_cancelled=False,
        ).select_related("room")

        reservation_map = {}
        for rsv in reservations:
            local_start = localtime(rsv.start_at)
            local_end = localtime(rsv.end_at)
            start_time = local_start.time()
            duration_min = int((local_end - local_start).total_seconds() / 60)
            span = max(1, duration_min // 30)
            reservation_map[(rsv.room_id, start_time)] = {
                "reservation": rsv,
                "span": span,
            }

        occupied = set()
        for (room_id, start_time), data in reservation_map.items():
            span = data["span"]
            for i, slot in enumerate(slots):
                if slot == start_time:
                    for j in range(1, span):
                        if i + j < len(slots):
                            occupied.add((room_id, slots[i + j]))
                    break

        grid = []
        for slot in slots:
            cells = []
            for room in rooms:
                if (room.id, slot) in occupied:
                    cells.append(
                        {"room": room, "reservation": None, "span": 1, "skip": True}
                    )
                else:
                    data = reservation_map.get((room.id, slot))
                    if data:
                        cells.append(
                            {
                                "room": room,
                                "reservation": data["reservation"],
                                "span": data["span"],
                                "skip": False,
                            }
                        )
                    else:
                        cells.append(
                            {
                                "room": room,
                                "reservation": None,
                                "span": 1,
                                "skip": False,
                            }
                        )
            grid.append({"slot": slot, "cells": cells})

        context.update(
            {
                "target_date": target_date,
                "prev_date": target_date - timedelta(days=1),
                "next_date": target_date + timedelta(days=1),
                "rooms": rooms,
                "grid": grid,
                "today": date.today(),
                "filter_value": filter_value,
                "departments": departments,
            }
        )
        return context


# F-06
class MyReservationListView(LoginRequiredMixin, ListView):
    model = Reservation
    template_name = "reservations/my_reservations.html"
    context_object_name = "reservations"

    def get_queryset(self):
        tab = self.request.GET.get("tab", "upcoming")
        now = timezone.now()

        if tab == "past":
            return (
                Reservation.objects.filter(user=self.request.user, start_at__lt=now)
                .select_related("room")
                .order_by("-start_at")
            )
        else:
            return (
                Reservation.objects.filter(
                    user=self.request.user, start_at__gte=now, is_cancelled=False
                )
                .select_related("room")
                .order_by("start_at")
            )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "upcoming")
        context["active_tab"] = tab

        now = timezone.now()
        context["upcoming_count"] = Reservation.objects.filter(
            user=self.request.user, start_at__gte=now, is_cancelled=False
        ).count()
        context["past_count"] = Reservation.objects.filter(
            user=self.request.user, start_at__lt=now
        ).count()
        return context


# F-09
class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.request.GET.get("room")
        selected_room = None
        if room_id:
            try:
                selected_room = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                selected_room = None
        context["selected_room"] = selected_room
        return context

    def get_initial(self):
        initial = super().get_initial()

        room_id = self.request.GET.get("room")
        if room_id:
            initial["room"] = room_id

        date_str = self.request.GET.get("date")
        time_str = self.request.GET.get("time")
        if date_str and time_str:
            try:
                start_at = datetime.strptime(
                    date_str + " " + time_str, "%Y-%m-%d %H:%M"
                )
                end_at = start_at + timedelta(minutes=30)
                initial["start_at"] = start_at
                initial["end_at"] = end_at
            except ValueError:
                pass

        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.reserved_by = self.request.user.name
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("reservation_detail", kwargs={"pk": self.object.pk})


# F-10
class ReservationDetailView(LoginRequiredMixin, DetailView):
    model = Reservation
    template_name = "reservations/detail.html"
    context_object_name = "reservation"


class ReservationUpdateView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = "reservations/edit.html"
    context_object_name = "reservation"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["room"].disabled = True
        return form

    def get_success_url(self):
        return reverse("reservation_detail", kwargs={"pk": self.object.pk})


@require_POST
@login_required
def reservation_cancel(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)

    if reservation.user != request.user:
        return redirect("calendar")

    reservation.is_cancelled = True
    reservation.save()

    return redirect("calendar")
