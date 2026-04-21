from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.utils import timezone

from reservations.models import Room, Reservation, Building, Facility
from accounts.models import Department
from .forms import RoomForm


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """is_staff=True のユーザーのみアクセスを許可する Mixin"""
    def test_func(self):
        return self.request.user.is_staff


def _list_context():
    """一覧テンプレート用の共通コンテキストを生成するヘルパー"""
    now = timezone.now()
    rooms = (
        Room.objects
        .select_related('building')
        .prefetch_related('facilities', 'departments')
        .order_by('name')
    )
    for room in rooms:
        room.future_reservation_count = Reservation.objects.filter(
            room=room,
            date__gte=now.date(),
        ).count()
        room.facility_ids = ','.join(
            str(pk) for pk in room.facilities.values_list('id', flat=True)
        )
        room.department_ids = ','.join(
            str(pk) for pk in room.departments.values_list('id', flat=True)
        )
    return {
        'rooms': rooms,
        'buildings': Building.objects.all().order_by('name'),
        'facilities': Facility.objects.all().order_by('name'),
        'departments': Department.objects.all().order_by('name'),
    }


# F-18: 会議室一覧
class RoomAdminListView(StaffRequiredMixin, ListView):
    model = Room
    template_name = 'admin_panel/room_admin_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return (
            Room.objects
            .select_related('building')
            .prefetch_related('facilities', 'departments')
            .order_by('name')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        for room in context['rooms']:
            room.future_reservation_count = Reservation.objects.filter(
                room=room,
                date__gte=now.date(),
            ).count()
            room.facility_ids = ','.join(
                str(pk) for pk in room.facilities.values_list('id', flat=True)
            )
            room.department_ids = ','.join(
                str(pk) for pk in room.departments.values_list('id', flat=True)
            )
        context.update({
            'form':        RoomForm(),
            'buildings':   Building.objects.all().order_by('name'),
            'facilities':  Facility.objects.all().order_by('name'),
            'departments': Department.objects.all().order_by('name'),
        })
        return context


# F-18: 会議室新規登録
class RoomCreateView(StaffRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/room_admin_list.html'
    success_url = reverse_lazy('room_admin_list')

    def form_invalid(self, form):
        ctx = _list_context()
        ctx.update({
            'form':                   form,
            'modal_open':             True,
            'modal_mode':             'create',
            'form_action_url':        reverse('room_create'),
            'selected_facility_ids':  [
                int(x) for x in form.data.getlist('facilities') if x.isdigit()
            ],
            'selected_department_ids': [
                int(x) for x in form.data.getlist('departments') if x.isdigit()
            ],
        })
        return render(self.request, 'admin_panel/room_admin_list.html', ctx)


# F-18: 会議室編集
class RoomUpdateView(StaffRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/room_admin_list.html'
    success_url = reverse_lazy('room_admin_list')

    def form_invalid(self, form):
        ctx = _list_context()
        ctx.update({
            'form':                   form,
            'modal_open':             True,
            'modal_mode':             'edit',
            'edit_room_id':           self.object.pk,
            'form_action_url':        reverse('room_edit', kwargs={'pk': self.object.pk}),
            'selected_facility_ids':  [
                int(x) for x in form.data.getlist('facilities') if x.isdigit()
            ],
            'selected_department_ids': [
                int(x) for x in form.data.getlist('departments') if x.isdigit()
            ],
        })
        return render(self.request, 'admin_panel/room_admin_list.html', ctx)


# F-19: 会議室削除（カスケード削除）
class RoomDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.delete()
        return redirect('room_admin_list')


# F-20: 利用停止 / 再開（is_active トグル）
class RoomToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.is_active = not room.is_active
        room.save(update_fields=['is_active'])
        return redirect('room_admin_list')
