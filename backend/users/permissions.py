from rest_framework.permissions import BasePermission
from rest_framework.permissions import IsAuthenticated, AllowAny

class IsOwnerOrReadOnly(BasePermission):
    message = "Это действие доступно только автору"

    def has_object_permission(self, request, view, obj):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True  
        if not request.user.is_authenticated and  obj == request.user:
            return True
        return False
    
class CustomIsAuthenticated(IsAuthenticated):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            self.message = (
                'Это действие доступно только авторизованным '
                + 'пользователям, пожалуйста, авторизуйтесь.')
            return False
        return True

