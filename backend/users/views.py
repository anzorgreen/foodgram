import base64

from django.core.files.base import ContentFile
from rest_framework import status, viewsets
from rest_framework.authentication import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.pagination import CustomPageNumberPagination
from core.permissions import IsOwnerOrReadOnly, StrictAuthenticated
from .models import User
from .serializers import (ChangePasswordSerializer, SubscriptionSerializer,
                          UserCreateSerializer, UserListSerializer,
                          UserWithRecipesSerializer)


class UserView(viewsets.ModelViewSet):
    """Представление для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return (AllowAny(),)
        elif self.action in (
            'update', 'partial_update', 'destroy', 'manage_avatar',
            'set_password'
        ):
            return (IsOwnerOrReadOnly(),)
        elif self.action == 'get_me':
            return (StrictAuthenticated(),)
        return (StrictAuthenticated(),)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ('get_subscriptions', 'subscribe'):
            return UserWithRecipesSerializer
        elif self.action in ('set_password'):
            return ChangePasswordSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='me')
    def get_me(self, request, pk=None):
        """Получить данные текущего пользователя."""
        return Response(self.get_serializer(request.user).data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def manage_avatar(self, request, pk=None):
        """Управление аватаром пользователя."""
        if request.method == 'PUT':
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {'detail': 'Поле "avatar" обязательно.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                format, imgstr = avatar_data.split(';base64,')
            except ValueError:
                return Response(
                    {'detail': 'Неверный формат аватара.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                img_data = base64.b64decode(imgstr)
            except Exception as e:
                return Response(
                    {'detail': f'Ошибка при декодировании аватара: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            avatar_file = ContentFile(img_data, name='avatar.png')
            if request.user.avatar:
                request.user.avatar.delete(save=False)
            request.user.avatar.save('avatar.png', avatar_file, save=True)
            avatar_url = request.build_absolute_uri(request.user.avatar.url)
            return Response(
                {'avatar': avatar_url},
                status=status.HTTP_200_OK
            )
        if not request.user.avatar:
            return Response(
                {'detail': 'Аватар не найден.'},
                status=status.HTTP_404_NOT_FOUND
            )
        request.user.avatar.delete()
        return Response(
            {'detail': 'Аватар успешно удален.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=('post', ), url_path='set_password')
    def set_password(self, request, pk=None):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST)
        new_password = serializer.validated_data['new_password']
        request.user.set_password(new_password)
        request.user.save()
        return Response(
            {'detail': 'Пароль успешно изменён.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['get'], url_path='subscriptions')
    def get_subscriptions(self, request):
        """Получить подписчиков пользователя."""
        users_i_follow = users_i_follow = User.objects.filter(
            subscribers__subscriber=request.user
        ).distinct()
        paginator = self.pagination_class()
        paginated_subscribers = paginator.paginate_queryset(
            users_i_follow, request
        )
        serializer = self.get_serializer(
            paginated_subscribers,
            many=True,
            context={
                'request': request,
                'recipes_limit': request.query_params.get('recipes_limit')
            }
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=True, methods=('post', 'delete'), url_path='subscribe')
    def subscribe(self, request, pk=None):
        """Подписаться на пользователя или отменить подписку."""
        serializer = SubscriptionSerializer(
            data={'subscribed_to': pk},
            context={'request': request}
        )
        if request.method == 'POST':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        serializer.is_valid(raise_exception=True)
        serializer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomObtainAuthToken(ObtainAuthToken):
    """Кастомный класс для аутентификации через email и пароль."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Обработка POST-запроса для аутентификации и создания токена."""
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'detail': 'Invalid credentials'}, status=400)
