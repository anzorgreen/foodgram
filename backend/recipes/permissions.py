from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Разрешение на чтение для всех и изменение только для автора."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return obj.author == request.user


class IsStaffOrReadOnly(BasePermission):
    """Разрешение на чтение для всех и изменение только администраторам."""

    def has_object_permission(self, request, view, obj):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_staff
