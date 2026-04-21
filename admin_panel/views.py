from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone

from reservations.models import Room, Reservation
from .forms import RoomForm


# ──────────────────────────────────────────────
# 管理者専用 Mixin（is_staff=True のユーザーのみ）
# ──────────────────────────────────────────────
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """is_staff=True のユーザーのみアクセスを許可する Mixin"""
    def test_func(self):
        return self.request.user.is_staff


# ──────────────────────────────────────────────
# F-18: 会議室一覧（管理者用）
# ──────────────────────────────────────────────
class RoomAdminListView(StaffRequiredMixin, ListView):
    model = Room
    template_name = 'admin_panel/room_admin_list.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return Room.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 各会議室の今後の予約件数を付与
        now = timezone.now()
        for room in context['rooms']:
            room.future_reservation_count = Reservation.objects.filter(
                room=room,
                date__gte=now.date(),
            ).count()
        return context


# ──────────────────────────────────────────────
# F-18: 会議室新規登録
# ──────────────────────────────────────────────
class RoomCreateView(StaffRequiredMixin, CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/room_admin_form.html'
    success_url = reverse_lazy('room_admin_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title']   = '会議室の新規登録'
        context['submit_label'] = '登録する'
        return context


# ──────────────────────────────────────────────
# F-18: 会議室編集
# ──────────────────────────────────────────────
class RoomUpdateView(StaffRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'admin_panel/room_admin_form.html'
    success_url = reverse_lazy('room_admin_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title']   = f'「{self.object.name}」の編集'
        context['submit_label'] = '更新する'
        return context


# ──────────────────────────────────────────────
# F-19: 会議室削除（カスケード削除）
# ──────────────────────────────────────────────
class RoomDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.delete()  # Reservation は on_delete=CASCADE で連鎖削除
        return redirect('room_admin_list')


# ──────────────────────────────────────────────
# F-20: 利用停止 / 再開（is_active トグル）
# ──────────────────────────────────────────────
class RoomToggleActiveView(StaffRequiredMixin, View):
    def post(self, request, pk):
        room = get_object_or_404(Room, pk=pk)
        room.is_active = not room.is_active
        room.save(update_fields=['is_active'])
        return redirect('room_admin_list')
