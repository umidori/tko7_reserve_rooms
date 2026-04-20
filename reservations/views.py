from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date, datetime, timedelta

from .models import Room, Reservation
from .forms import RoomForm


def home(request):
    return HttpResponse("会議室予約システム")


# ──────────────────────────────────────────────
# 管理者専用 Mixin（is_staff=True のユーザーのみ）
# ──────────────────────────────────────────────
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """is_staff=True のユーザーのみアクセスを許可する Mixin"""
    def test_func(self):
        return self.request.user.is_staff

# ──────────────────────────────────────────────
# F-04：日付を受け取る
# ──────────────────────────────────────────────
class CalendarView(LoginRequiredMixin, TemplateView):
    template_name = 'reservations/calendar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # GETパラメータ ?date=YYYY-MM-DD を受け取る
        date_str = self.request.GET.get('date')
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            target_date = date.today()  # 不正な値なら当日にフォールバック

        filter_mode = self.request.GET.get('filter', 'all')  # TODO: 所属モデル実装後に 'dept' をデフォルトにする

        # is_active=True の会議室のみ取得（利用停止中は除外）
        # TODO: 所属（Department）モデルと department_rooms が実装されたら
        #       filter_mode == 'dept' の分岐でユーザーの所属に紐づく会議室を絞り込む
        rooms = Room.objects.filter(is_active=True).order_by('name')

        # 00:00〜23:30 を 30 分刻みで生成する
        slots = []
        current = datetime.combine(target_date, datetime.min.time())  # 当日00:00
        end_of_day = current.replace(hour=23, minute=30)
        while current <= end_of_day:
            slots.append(current.time())   # time オブジェクト（例: 09:00）
            current += timedelta(minutes=30)

        # 当日・キャンセルされていない予約を全件取得
        reservations = Reservation.objects.filter(
            date=target_date,
        ).select_related('room')

        # {(room_id, start_time): reservation} の辞書を作成
        reservation_map = {}
        for rsv in reservations:
            reservation_map[(rsv.room_id, rsv.start_time)] = rsv

        # テンプレートが使いやすいよう、2次元リストに変換する
        # grid = [ {slot, cells: [{room, reservation or None}]} ]
        grid = []
        for slot in slots:
            cells = []
            for room in rooms:
                rsv = reservation_map.get((room.id, slot))
                cells.append({'room': room, 'reservation': rsv})
            grid.append({'slot': slot, 'cells': cells})

        context.update({
            'target_date': target_date,
            'prev_date': target_date - timedelta(days=1),
            'next_date': target_date + timedelta(days=1),
            'rooms': rooms,
            'grid': grid,
            'today': date.today(),
            'filter_mode': filter_mode,
        })
        return context

# ──────────────────────────────────────────────
# F-18: 会議室一覧（管理者用）
# ──────────────────────────────────────────────
class RoomAdminListView(StaffRequiredMixin, ListView):
    model = Room
    template_name = 'rooms/room_admin_list.html'
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
    template_name = 'rooms/room_admin_form.html'
    success_url = reverse_lazy('room_admin_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title']  = '会議室の新規登録'
        context['submit_label'] = '登録する'
        return context


# ──────────────────────────────────────────────
# F-18: 会議室編集
# ──────────────────────────────────────────────
class RoomUpdateView(StaffRequiredMixin, UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'rooms/room_admin_form.html'
    success_url = reverse_lazy('room_admin_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title']  = f'「{self.object.name}」の編集'
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
