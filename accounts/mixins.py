from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """role='admin' かつ is_active=True のユーザーのみアクセスを許可する Mixin
    - 未認証 → LOGIN_URL へリダイレクト（LoginRequiredMixin が処理）
    - role != 'admin' または is_active=False → 403 Forbidden（UserPassesTestMixin が処理）
    """
    def test_func(self):
        user = self.request.user
        return user.is_active and user.role == 'admin'
