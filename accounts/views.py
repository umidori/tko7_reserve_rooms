import logging

from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import EmailAuthenticationForm, UserCreateForm, UserUpdateForm
from .mixins import AdminRequiredMixin
from .models import User

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────
# ログイン（既存）
# ─────────────────────────────────────────────────────────────
class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = EmailAuthenticationForm


# ─────────────────────────────────────────────────────────────
# F-14: ユーザー一覧（管理者専用）
# ─────────────────────────────────────────────────────────────
class UserListView(AdminRequiredMixin, ListView):
    """全ユーザーを一覧表示する（is_active 問わず）。"""
    model = User
    template_name = 'accounts/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = User.objects.select_related('department').order_by('login_id')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(name__icontains=q)
            logger.info("UserListView: search q=%s matched %s", q, qs.count())
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['total_count'] = User.objects.count()
        return context


# ─────────────────────────────────────────────────────────────
# F-15: ユーザー追加（管理者専用）
# ─────────────────────────────────────────────────────────────
class UserCreateView(AdminRequiredMixin, CreateView):
    """ユーザーを新規作成する。初期パスワードは 'Bold1234'。"""
    model = User
    form_class = UserCreateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_admin_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password('Bold1234')
        user.is_active = True
        user.save()
        logger.info(
            "User created: login_id=%s by admin=%s",
            user.login_id,
            self.request.user.login_id,
        )
        messages.success(self.request, f'ユーザー「{user.name}」を追加しました。')
        return redirect(self.success_url)

    def form_invalid(self, form):
        logger.warning("UserCreateForm invalid: errors=%s", form.errors)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = True
        context['page_title'] = 'ユーザーを追加'
        return context


# ─────────────────────────────────────────────────────────────
# F-15: ユーザー編集（管理者専用）
# ─────────────────────────────────────────────────────────────
class UserUpdateView(AdminRequiredMixin, UpdateView):
    """ユーザーの name / role / department を編集する（login_id は変更不可）。"""
    model = User
    form_class = UserUpdateForm
    template_name = 'accounts/user_form.html'
    success_url = reverse_lazy('user_admin_list')

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def form_valid(self, form):
        user = form.save()
        logger.info(
            "User updated: login_id=%s by admin=%s",
            user.login_id,
            self.request.user.login_id,
        )
        messages.success(self.request, f'ユーザー「{user.name}」の情報を更新しました。')
        return redirect(self.success_url)

    def form_invalid(self, form):
        logger.warning("UserUpdateForm invalid: errors=%s", form.errors)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_create'] = False
        context['page_title'] = 'ユーザーを編集'
        return context


# ─────────────────────────────────────────────────────────────
# F-16: ユーザー有効化 / 無効化トグル（管理者専用）
# ─────────────────────────────────────────────────────────────
class UserToggleActiveView(AdminRequiredMixin, View):
    """is_active をトグルする。自己無効化は拒否する。POST のみ受け付ける。"""

    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)

        if request.user.pk == target.pk:
            messages.error(request, '自分自身を無効化することはできません。')
            logger.warning(
                "Self-deactivation attempt: admin=%s",
                request.user.login_id,
            )
            return redirect('user_admin_list')

        target.is_active = not target.is_active
        target.save(update_fields=['is_active', 'updated_at'])

        action = '有効化' if target.is_active else '無効化'
        logger.info(
            "User %s: login_id=%s by admin=%s",
            action,
            target.login_id,
            request.user.login_id,
        )
        messages.success(request, f'ユーザー「{target.name}」を{action}しました。')
        return redirect('user_admin_list')
