from rest_framework.permissions import BasePermission, IsAuthenticated


class ActionBasedPermission(BasePermission):
    """Универсальное разрешение с настройкой прав для разных методов."""

    def has_permission(self, request, view):
        default = request.method in ['GET', 'HEAD', 'OPTIONS']
        return getattr(
            view,
            'permission_rules',
            {}
        ).get(request.method, default)


class IsOwnerOrReadOnly(BasePermission):
    """Разрешение на чтение для всех и изменение только владельцу."""

    message = "Это действие доступно только автору"

    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        owner = getattr(obj, 'author', None) or getattr(obj, 'user', None)
        return owner == request.user

    def has_permission(self, request, view):
        return request.user.is_authenticated or request.method in [
            'GET', 'HEAD', 'OPTIONS'
        ]


class IsStaffOrReadOnly(BasePermission):
    """Разрешение на чтение для всех и изменение только администраторам."""

    message = "Это действие доступно только администраторам"

    def has_permission(self, request, view):
        return (
            request.method in ['GET', 'HEAD', 'OPTIONS']
            or (request.user and request.user.is_staff)
        )


class StrictAuthenticated(IsAuthenticated):
    """Строгая аутентификация с кастомным сообщением."""

    message = "Требуется авторизация для выполнения этого действия"
