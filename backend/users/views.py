import base64
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsOwnerOrReadOnly, CustomIsAuthenticated, AllowAny
from .serializers import (
    UserCreateSerializer, UserListSerializer, UserWithRecipesSerializer
)
from constants import ITEMS_ON_PAGE
from rest_framework.pagination import PageNumberPagination
from .models import User
from pagination import CustomPageNumberPagination

class UserView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserListSerializer
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create']:
            return (AllowAny(),)
        elif self.action in ['update', 'partial_update', 'destroy', 'manage_avatar', 'set_password']:
            return (IsOwnerOrReadOnly(),)
        elif self.action == 'get_me':
            return (CustomIsAuthenticated(),)
        return (CustomIsAuthenticated(),)
    
    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return UserListSerializer
        elif self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['get_subscribers', 'subscribe']:
            return UserWithRecipesSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=['get'], url_path='me')
    def get_me(self, request, pk=None):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def manage_avatar(self, request, pk=None):
        if request.method == 'PUT':
            user = request.user
            avatar_data = request.data.get('avatar')
            if not avatar_data:
                return Response(
                    {"detail": "Поле 'avatar' обязательно."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                format, imgstr = avatar_data.split(';base64,')
                img_data = base64.b64decode(imgstr)
                file_name = 'avatar.png'
                avatar_file = ContentFile(img_data, name=file_name)
                if user.avatar:
                    user.avatar.delete(save=False)
                user.avatar.save(file_name, avatar_file, save=True)
                avatar_url = request.build_absolute_uri(user.avatar.url)
                return Response(
                    {
                        "avatar": avatar_url
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"detail": f"Ошибка при обработке аватара: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        elif request.method == 'DELETE':
            user = request.user
            if not user.avatar:
                return Response(
                    {"detail": "Аватар не найден."},
                    status=status.HTTP_404_NOT_FOUND
                )
            user.avatar.delete()
            return Response(
                {"detail": "Аватар успешно удален."},
                status=status.HTTP_204_NO_CONTENT
            )
    @action(detail=False, methods=['post',], url_path='set_password')
    def set_password(self, request, pk=None):
        new_password = request.data.get('new_password')
        current_password = request.data.get('current_password')
        user = request.user
        if not user.check_password(current_password):
            return Response(
                {"detail": "Неверный текущий пароль."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(new_password)
        user.save()
        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_204_NO_CONTENT
        )
    
    @action(detail=False, methods=['get'], url_path='subscriptions')
    def get_subscribers(self, request):
        user = request.user
        subscribers = user.subscribers.all()
        subscriber_users = [subscriber.subscriber for subscriber in subscribers]

        paginator = self.pagination_class()
        paginated_subscribers = paginator.paginate_queryset(subscriber_users, request)
        recipes_limit = request.query_params.get('recipes_limit')
        serializer = self.get_serializer(
            paginated_subscribers,
            many=True,
            context={
                'request': request,
                'recipes_limit': recipes_limit
            })
        return paginator.get_paginated_response(serializer.data)
        # paginator.page_size = self.pagination_class.page_size if self.pagination_class else ITEMS_ON_PAGE
            
    @action(detail=True, methods=['post', 'delete'], url_path='subscribe')
    def subscribe(self, request, pk=None):
        user = request.user
        subscribe_to = get_object_or_404(User, id=pk)
        from cart.models import Subsrciption
        if request.method == "POST":
            if Subsrciption.objects.filter(
                subscriber=user, subscribed_to=subscribe_to
                ).exists():
                return Response(
                    {"detail": "Вы уже подписанный на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            elif user == subscribe_to:
                return Response(
                    {"detail": "Вы не можете подписаться на сомого себя"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subsrciption.objects.create(
                subscriber=user,
                subscribed_to=subscribe_to)
            recipes_limit = request.query_params.get('recipes_limit')
            serializer = UserWithRecipesSerializer(
                subscribe_to,
                many=False,
                context={
                    'request': request,
                    'recipes_limit': recipes_limit
                }
            )
            response_data = serializer.data
            response_data['is_subscribed'] = True
            return Response(
                response_data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == "DELETE":
            if not Subsrciption.objects.filter(
                subscriber=user, subscribed_to=subscribe_to
                ).exists():
                return Response(
                    {"detail": "Вы не подписанны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subsrciption.objects.filter(
                subscriber=user, subscribed_to=subscribe_to
                ).delete()
            return Response(
                status=status.HTTP_204_NO_CONTENT
            )
    