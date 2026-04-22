import logging

from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
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
# ヘルパー：一覧テンプレート用の共通コンテキスト
# （form_invalid 時にモーダルを開いた状態で一覧を再描画するために使用）
# ─────────────────────────────────────────────────────────────
def _user_list_context(request, **extra):
    qs = User.objects.select_related('department').order_by('login_id')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(name__icontains=q)
    default_form = UserCreateForm()
    ctx = {
        'users': qs,
        'q': q,
        'total_count': User.objects.count(),
        # モーダル内で描画するフォーム（エラーがない場合は空の追加フォーム）
        'modal_form': default_form,
        'modal_open': False,
        'modal_mode': 'create',
        'form_action_url': None,
        'edit_user_id': None,
        'edit_user_login_id': '',
        # _user_list_context 経由の再描画ではページネーションなし
        'is_paginated': False,
    }
    ctx.update(extra)
    return ctx


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
        # モーダル用（通常表示時は空の追加フォーム）
        context['modal_form'] = UserCreateForm()
        context['modal_open'] = False
        context['modal_mode'] = 'create'
        context['form_action_url'] = None
        context['edit_user_id'] = None
        context['edit_user_login_id'] = ''
        return context


# ─────────────────────────────────────────────────────────────
# F-15: ユーザー追加（管理者専用）
# ─────────────────────────────────────────────────────────────
class UserCreateView(AdminRequiredMixin, CreateView):
    """ユーザーを新規作成する。初期パスワードは 'Bold1234'。
    モーダル経由の POST のみ処理。GET は一覧にリダイレクト。
    """
    model = User
    form_class = UserCreateForm
    success_url = reverse_lazy('user_admin_list')

    def get(self, request, *args, **kwargs):
        # モーダル経由でのみ使用するため直接アクセスはリダイレクト
        return redirect('user_admin_list')

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
        ctx = _user_list_context(
            self.request,
            modal_form=form,
            modal_open=True,
            modal_mode='create',
            form_action_url=reverse('user_create'),
        )
        return render(self.request, 'accounts/user_list.html', ctx)


# ─────────────────────────────────────────────────────────────
# F-15: ユーザー編集（管理者専用）
# ─────────────────────────────────────────────────────────────
class UserUpdateView(AdminRequiredMixin, UpdateView):
    """ユーザーの name / role / department を編集する（login_id は変更不可）。
    モーダル経由の POST のみ処理。GET は一覧にリダイレクト。
    """
    model = User
    form_class = UserUpdateForm
    success_url = reverse_lazy('user_admin_list')

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        return redirect('user_admin_list')

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
        obj = self.get_object()
        ctx = _user_list_context(
            self.request,
            modal_form=form,
            modal_open=True,
            modal_mode='edit',
            edit_user_id=obj.pk,
            edit_user_login_id=obj.login_id,
            form_action_url=reverse('user_edit', kwargs={'pk': obj.pk}),
        )
        return render(self.request, 'accounts/user_list.html', ctx)


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
