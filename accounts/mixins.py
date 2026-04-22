import logging

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

logger = logging.getLogger(__name__)


class AdminRequiredMixin(LoginRequiredMixin):
    """管理者専用アクセス制御 Mixin（F-14〜F-16, F-18〜F-20 共通）"""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if request.user.role != 'admin' or not request.user.is_active:
            logger.warning(
                "PermissionDenied: user=%s role=%s is_active=%s path=%s",
                getattr(request.user, 'login_id', request.user.pk),
                getattr(request.user, 'role', None),
                request.user.is_active,
                request.path,
            )
            raise PermissionDenied

        return super().dispatch(request, *args, **kwargs)
    
    """role='admin' かつ is_active=True のユーザーのみアクセスを許可する Mixin
    - 未認証 → LOGIN_URL へリダイレクト（LoginRequiredMixin が処理）
    - role != 'admin' または is_active=False → 403 Forbidden（UserPassesTestMixin が処理）
    """
    def test_func(self):
        user = self.request.user
        return user.is_active and user.role == 'admin'