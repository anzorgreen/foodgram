from rest_framework import serializers
from djoser.serializers import TokenCreateSerializer
from .models import User, Subscription
from recipes.models import Recipe
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password


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

    id = serializers.IntegerField(read_only=True)
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
    first_name = serializers.CharField(max_length=150, required=True)
    last_name = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(write_only=True, required=True)

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


class UserWithRecipesSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя с его рецептами и подпиской."""

    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)
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
        return Recipe.objects.filter(author=obj).count()

    def get_is_subscribed(self, obj):
        """Проверка, подписан ли текущий пользователь на данного автора."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subscription.objects.filter(
            subscriber=request.user, subscribed_to=obj).exists()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name', 'last_name',
            'is_subscribed', 'recipes', 'recipes_count', 'avatar',
        )
