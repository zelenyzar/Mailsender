from django.http import HttpResponseForbidden
from django.contrib.auth import get_user_model

User = get_user_model()


def is_manager(user):
    return bool(
        user
        and user.is_authenticated
        and user.groups.filter(name='manager').exists()
    )


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
        if is_manager(self.request.user):
            return True
        obj = self.get_object()
        return obj.owner_id == self.request.user.pk
