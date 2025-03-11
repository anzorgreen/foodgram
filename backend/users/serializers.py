from rest_framework import serializers
from djoser.serializers import TokenCreateSerializer
from .models import User
from cart.models import Subsrciption
from recipes.models import Recipe
from django.core.validators import RegexValidator
from rest_framework.validators import UniqueValidator
from django.contrib.auth.hashers import make_password



class UserListSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subsrciption.objects.filter(
            subscriber=request.user, subscribed_to=obj).exists()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

class UserCreateSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        read_only=True
    )
    email = serializers.EmailField(
        max_length=254,
        required=True,
        error_messages={
            'required': 'Укажите ваш адрес электронной почты.',
            'blank': 'Поле электронной почты не может быть пустым.',
            'invalid': 'Введите корректный адрес электронной почты.',
        },
        validators=[UniqueValidator(
            queryset=User.objects.all(),
            message=('Это этот адрес почты уже зарегистрирован'))
        ]
    )
    username = serializers.CharField(
        max_length=150,
        required=True,
        error_messages={
            'required': 'Укажите ваш адрес электронной почты.',
            'blank': 'Поле электронной почты не может быть пустым.',
            'invalid': 'Введите корректный адрес электронной почты.',
        },
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message=('Имя пользователя может содержать буквы, цифры, '
                         + 'а также следующие символы: . @ + - ')
            ),
            UniqueValidator(
                queryset=User.objects.all(),
                message=('Это имя пользователя занято'))
            
        ]
    )
    first_name = serializers.CharField(
        max_length=150,
        required=True,
        error_messages={
            'required': 'Укажите ваш адрес электронной почты.',
            'blank': 'Поле электронной почты не может быть пустым.',
            'invalid': 'Введите корректный адрес электронной почты.',
        }
    )
    last_name = serializers.CharField(
        max_length=150,
        required=True,
        error_messages={
            'required': 'Укажите ваш адрес электронной почты.',
            'blank': 'Поле электронной почты не может быть пустым.',
            'invalid': 'Введите корректный адрес электронной почты.',
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            'required': 'Укажите ваш пароль',
            'blank': 'Пароль не может быть пустым',
            'invalid': 'Введите корректный пароль',
        }
    
    )


    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password',
        )
    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class CustomTokenCreateSerializer(TokenCreateSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'password',)

class UserWithRecipesSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    avatar = serializers.ImageField(required=False)
    recipes_count = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            try:
                recipes_limit = int(recipes_limit)
                recipes = recipes[:recipes_limit]
            except ValueError:
                make_password
        from recipes.serializers import RecipeBriefSerializer
        return RecipeBriefSerializer(recipes, many=True).data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Subsrciption.objects.filter(
            subscriber=request.user, subscribed_to=obj).exists()
    
    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )