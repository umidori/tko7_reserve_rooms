from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from reservations.models import Room, Facility, Building
from .forms import RoomSearchForm


class RoomListView(LoginRequiredMixin, ListView):
    """F-07: 会議室一覧表示 / F-08: 会議室絞り込み検索 (S-04)"""

    model = Room
    template_name = "rooms/room_list.html"
    context_object_name = "rooms"

    def get_queryset(self):
        qs = (
            Room.objects.select_related("building")
            .prefetch_related("facilities")
            .order_by("name")
        )

        form = self._get_bound_form()

        # バリデーション通過時のみフィルター適用
        # （不正値はフィルターなし扱い）
        if form.is_valid():
            capacity = form.cleaned_data.get("capacity")
            facility_qs = form.cleaned_data.get("facility")
            building = form.cleaned_data.get("building")
            floor = form.cleaned_data.get("floor")

            if capacity:
                qs = qs.filter(capacity__gte=capacity)

            if facility_qs:
                for fac in facility_qs:
                    qs = qs.filter(facilities__id=fac.id)

            if building:
                qs = qs.filter(building=building)

            if floor:
                qs = qs.filter(floor=floor)

        # 設備フィルターで JOIN が発生するため distinct() を付与
        return qs.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = self._get_bound_form()

        # フィルター条件が1つでも指定されているか判定
        is_filtered = False
        if self.request.GET:
            params = self.request.GET
            if (
                params.get("capacity")
                or params.getlist("facility")
                or params.get("building")
                or params.get("floor")
            ):
                is_filtered = True

        context.update(
            {
                "form": form,
                "facilities": Facility.objects.all().order_by("name"),
                "buildings": Building.objects.all().order_by("name"),
                "is_filtered": is_filtered,
            }
        )
        return context

    def _get_bound_form(self):
        """GETパラメータからフォームを生成するヘルパー"""
        if self.request.GET:
            return RoomSearchForm(self.request.GET)
        return RoomSearchForm()
