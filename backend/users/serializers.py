from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.shortcuts import get_object_or_404
from djoser.serializers import TokenCreateSerializer
from recipes.models import Recipe
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from backend.settings import MAX_LENTHG_SHORT_NAME

from .models import Subscription, User


class UserListSerializer(serializers.ModelSerializer):
    """Сериализатор для списка пользователей с проверкой подписки."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)

    def get_is_subscribed(self, obj):
        """Проверка, подписан ли пользователь на данного автора."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscriber=request.user, subscribed_to=obj).exists()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'avatar',
        )


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя."""

    email = serializers.EmailField(
        max_length=254,
        required=True,
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message='Этот адрес почты уже зарегистрирован'
        )]
    )
    username = serializers.CharField(
        max_length=150,
        required=True,
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=(
                    'Имя пользователя может содержать'
                    ' буквы, цифры и следующие символы: . @ + -'
                )
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message='Это имя пользователя занято'
            )
        ]
    )
    first_name = serializers.CharField(
        max_length=MAX_LENTHG_SHORT_NAME,
        required=True
    )
    last_name = serializers.CharField(
        max_length=MAX_LENTHG_SHORT_NAME,
        required=True
    )
    password = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name', 'password'
        )

    def validate_password(self, value):
        """Валидация пароля на сложность."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(
                {'password': list(e.messages)}
            )
        return value

    def create(self, validated_data):
        """Хеширование пароля перед сохранением пользователя."""
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)


class CustomTokenCreateSerializer(TokenCreateSerializer):
    """Сериализатор для создания токена авторизации по email и паролю."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'password')


class UserWithRecipesSerializer(UserListSerializer):
    """Сериализатор для пользователя с его рецептами и подпиской."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        """Получение рецептов пользователя с учетом лимита."""
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                pass
        from recipes.serializers import RecipeBriefSerializer
        return RecipeBriefSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        """Получение количества рецептов пользователя."""
        return obj.recipes.count()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar',
        )


class ChangePasswordSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения пароля."""

    new_password = serializers.CharField(style={'input_type': 'password'})
    current_password = serializers.CharField(style={'input_type': 'password'})

    class Meta:
        model = User
        fields = (
            'current_password', 'new_password'
        )

    def validate_new_password(self, value):
        """Валидация нового пароля."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(
                {'new_password': list(e.messages)}
            )
        return value

    def validate(self, data):
        """Валидация текущего пароля и проверка на совпадение."""
        request = self.context.get('request')
        user = request.user

        if not user.check_password(data['current_password']):
            raise serializers.ValidationError({
                'current_password': "Старый пароль неверный"
            })
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({
                'new_password': "Новый пароль не должен совпадать с текущим"
            })
        return data


class SubscriptionSerializer(serializers.Serializer):
    """Сериализатор для создания создания и удаления подписки."""

    subscribed_to = serializers.IntegerField(
        write_only=True
    )

    def validate_subscribed_to(self, value):
        """Проверяем, что пользователь существует и не является текущим."""
        user = self.context['request'].user
        subscribe_to = get_object_or_404(User, id=value)

        if user == subscribe_to:
            raise serializers.ValidationError(
                "Вы не можете подписаться на самого себя"
            )
        return subscribe_to

    def create(self, validated_data):
        """Создаем подписку."""
        user = self.context['request'].user
        subscribe_to = validated_data['subscribed_to']

        if Subscription.objects.filter(
            subscriber=user,
            subscribed_to=subscribe_to
        ).exists():
            raise serializers.ValidationError(
                "Вы уже подписаны на этого пользователя"
            )

        return Subscription.objects.create(
            subscriber=user,
            subscribed_to=subscribe_to
        )

    def delete(self):
        """Удаляем подписку."""
        user = self.context['request'].user
        subscribe_to = self.validated_data['subscribed_to']

        subscription = Subscription.objects.filter(
            subscriber=user,
            subscribed_to=subscribe_to
        )
        if not subscription.exists():
            raise serializers.ValidationError(
                "Вы не подписаны на этого пользователя"
            )
        subscription.delete()
