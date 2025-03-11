from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, AllowAny

class IsOwnerOrReadOnly(BasePermission):
    message = "Это действие доступно только автору"

    def has_object_permission(self, request, view, obj):
        return (request.method in ['GET', 'HEAD', 'OPTIONS'] 
            or (request.user.is_authenticated and obj == request.user))

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                or request.method in ['GET', 'HEAD', 'OPTIONS'])

    
class CustomIsAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            self.message = (
                'Это действие доступно только авторизованным '
                + 'пользователям, пожалуйста, авторизуйтесь.')
            return False
        return True
    
class IsAdmin(BasePermission):
    message = "Это действие доступно только администраторам."

    def has_permission(self, request, view):
        return request.user and request.user.is_staff
