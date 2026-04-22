import logging

from django.contrib.auth.mixins import LoginRequiredMixin
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
