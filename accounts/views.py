import csv
import io
import logging

from django.contrib import messages
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, ListView, UpdateView

from .forms import CSVUploadForm, EmailAuthenticationForm, UserCreateForm, UserUpdateForm
from .mixins import AdminRequiredMixin
from .models import Department, User

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    authentication_form = EmailAuthenticationForm


# パスワード変更
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change.html'
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        messages.success(self.request, 'パスワードを変更しました。')
        return super().form_valid(form)


def _user_list_context(request, **extra):
    qs = User.objects.select_related('department').order_by('login_id')
    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(name__icontains=q)
    ctx = {
        'users': qs,
        'q': q,
        'total_count': User.objects.count(),
        'modal_form': UserCreateForm(),
        'modal_open': False,
        'modal_mode': 'create',
        'form_action_url': None,
        'edit_user_id': None,
        'edit_user_login_id': '',
        'is_paginated': False,
    }
    ctx.update(extra)
    return ctx


# F-14
class UserListView(AdminRequiredMixin, ListView):
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
        context['modal_form'] = UserCreateForm()
        context['modal_open'] = False
        context['modal_mode'] = 'create'
        context['form_action_url'] = None
        context['edit_user_id'] = None
        context['edit_user_login_id'] = ''
        return context


# F-15 Create
class UserCreateView(AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    success_url = reverse_lazy('user_admin_list')

    def get(self, request, *args, **kwargs):
        return redirect('user_admin_list')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password('Bold1234')
        user.is_active = True
        user.save()
        logger.info("User created: login_id=%s by admin=%s", user.login_id, self.request.user.login_id)
        messages.success(self.request, 'ユーザー「{}」を追加しました。'.format(user.name))
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


# F-15 Update
class UserUpdateView(AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    success_url = reverse_lazy('user_admin_list')

    def get_object(self, queryset=None):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def get(self, request, *args, **kwargs):
        return redirect('user_admin_list')

    def form_valid(self, form):
        user = form.save()
        logger.info("User updated: login_id=%s by admin=%s", user.login_id, self.request.user.login_id)
        messages.success(self.request, 'ユーザー「{}」の情報を更新しました。'.format(user.name))
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


# F-16
class UserToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        target = get_object_or_404(User, pk=pk)

        if request.user.pk == target.pk:
            messages.error(request, '自分自身を無効化することはできません。')
            logger.warning("Self-deactivation attempt: admin=%s", request.user.login_id)
            return redirect('user_admin_list')

        target.is_active = not target.is_active
        target.save(update_fields=['is_active', 'updated_at'])

        action = '有効化' if target.is_active else '無効化'
        logger.info("User %s: login_id=%s by admin=%s", action, target.login_id, request.user.login_id)
        messages.success(request, 'ユーザー「{}」を{}しました。'.format(target.name, action))
        return redirect('user_admin_list')


# F-17
SESSION_KEY_CSV_PREVIEW = 'csv_preview_data'


class CSVImportView(AdminRequiredMixin, View):
    template_name = 'accounts/csv_import.html'

    @staticmethod
    def _decode_csv(raw):
        try:
            import chardet
            detected = chardet.detect(raw)
            encoding = detected.get('encoding') or 'utf-8'
        except ImportError:
            encoding = 'utf-8'
        try:
            return raw.decode(encoding)
        except (UnicodeDecodeError, LookupError):
            return raw.decode('cp932', errors='replace')

    @staticmethod
    def _parse_csv(text):
        reader = csv.reader(io.StringIO(text))
        rows_raw = list(reader)
        if not rows_raw:
            return []

        data_rows = rows_raw[1:]  # skip header

        csv_login_ids = [r[0].strip() for r in data_rows if len(r) > 0 and r[0].strip()]
        existing_ids = set(
            User.objects.filter(login_id__in=csv_login_ids).values_list('login_id', flat=True)
        )

        preview_rows = []
        for i, row in enumerate(data_rows, start=2):
            login_id  = row[0].strip() if len(row) > 0 else ''
            name      = row[1].strip() if len(row) > 1 else ''
            role      = row[2].strip() if len(row) > 2 else ''
            dept_name = row[3].strip() if len(row) > 3 else ''

            error_msg = ''
            if not login_id or not name:
                error_msg = '必須項目が不足しています'
            elif role not in ('admin', 'user'):
                error_msg = '権限の値が不正です（admin または user）'
            elif login_id in existing_ids:
                error_msg = 'このユーザーIDはすでに存在します'

            preview_rows.append({
                'row_num':   i,
                'login_id':  login_id,
                'name':      name,
                'role':      role,
                'dept_name': dept_name,
                'is_valid':  error_msg == '',
                'error':     error_msg,
            })

        return preview_rows

    def get(self, request, *args, **kwargs):
        request.session.pop(SESSION_KEY_CSV_PREVIEW, None)
        return render(request, self.template_name, {'form': CSVUploadForm()})

    def post(self, request, *args, **kwargs):
        form = CSVUploadForm(request.POST, request.FILES)
        if not form.is_valid():
            return render(request, self.template_name, {'form': form})

        csv_file = form.cleaned_data['csv_file']
        filename = csv_file.name

        try:
            raw = csv_file.read()
            text = self._decode_csv(raw)
            preview_rows = self._parse_csv(text)
        except Exception as exc:
            logger.error("CSV parse error. admin_id=%s filename=%s detail=%s", request.user.pk, filename, exc)
            form.add_error(None, 'CSVファイルの読み込みに失敗しました。')
            return render(request, self.template_name, {'form': form})

        request.session[SESSION_KEY_CSV_PREVIEW] = preview_rows

        valid_count = sum(1 for r in preview_rows if r['is_valid'])
        error_count = len(preview_rows) - valid_count

        if error_count > 0:
            logger.warning("CSV import skipped rows=%s admin_id=%s", error_count, request.user.pk)

        return render(request, self.template_name, {
            'form':         CSVUploadForm(),
            'preview_rows': preview_rows,
            'valid_count':  valid_count,
            'error_count':  error_count,
            'filename':     filename,
        })


class CSVImportExecuteView(AdminRequiredMixin, View):
    http_method_names = ['post']

    def post(self, request, *args, **kwargs):
        preview_rows = request.session.get(SESSION_KEY_CSV_PREVIEW)

        if not preview_rows:
            messages.error(request, 'セッションが切れました。再度CSVをアップロードしてください。')
            return redirect('csv_import')

        valid_rows = [r for r in preview_rows if r['is_valid']]
        skip_count = len(preview_rows) - len(valid_rows)
        users_to_create = []

        try:
            with transaction.atomic():
                for row in valid_rows:
                    dept = None
                    if row['dept_name']:
                        dept, created = Department.objects.get_or_create(name=row['dept_name'])
                        if created:
                            logger.info("Department created during CSV import. name=%s admin_id=%s",
                                        row['dept_name'], request.user.pk)
                    u = User(
                        login_id=row['login_id'],
                        name=row['name'],
                        role=row['role'],
                        department=dept,
                        is_active=True,
                    )
                    u.set_password('Bold1234')
                    users_to_create.append(u)

                User.objects.bulk_create(users_to_create)

        except Exception as exc:
            logger.error("CSV import bulk_create failed. admin_id=%s detail=%s", request.user.pk, exc)
            messages.error(request, 'インポート中にエラーが発生しました。管理者に連絡してください。')
            return redirect('csv_import')

        success_count = len(users_to_create)
        request.session.pop(SESSION_KEY_CSV_PREVIEW, None)

        logger.info("CSV import completed. success=%s skip=%s admin_id=%s",
                    success_count, skip_count, request.user.pk)
        messages.success(
            request,
            '登録成功：{}件、スキップ（エラー）：{}件'.format(success_count, skip_count),
        )
        return redirect('user_admin_list')
