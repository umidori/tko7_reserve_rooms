from django.http import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date, datetime, timedelta

from .models import Room, Reservation
from .forms import RoomForm, ReservationForm


def home(request):
    return HttpResponse("会議室予約システム")


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
            start_at__date=target_date,
            is_cancelled=False,
        ).select_related('room')

        # {(room_id, start_time): reservation} の辞書を作成
        reservation_map = {}
        for rsv in reservations:
            reservation_map[(rsv.room_id, rsv.start_at.time())] = rsv

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

class ReservationCreateView(CreateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'reservations/create.html'
    success_url = reverse_lazy('calendar')  # 遷移先

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        room_id = self.request.GET.get('room')

        selected_room = None
        if room_id:
            try:
                selected_room = Room.objects.get(id=room_id)
            except Room.DoesNotExist:
                selected_room = None

        context['selected_room'] = selected_room
        return context

    def get_initial(self):
        initial = super().get_initial()
        room_id = self.request.GET.get('room')
        if room_id:
            initial['room'] = room_id
        return initial
    
    def form_valid(self, form):
        # ログインユーザーを自動設定
        form.instance.user = self.request.user
        return super().form_valid(form)
