# mailing/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .permissions import is_manager


class OwnerOrManagerMixin(LoginRequiredMixin):
    """Для list/detail: менеджер видит всё, остальные — только свои объекты."""

    def get_queryset(self):
        qs = super().get_queryset()
        if is_manager(self.request.user):
            return qs
        return qs.filter(owner=self.request.user)


class OwnerCheckMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Для update/delete: разрешено только владельцу или менеджеру."""

    def test_func(self):
        obj = self.get_object()
        return obj.owner_id == self.request.user.pk
