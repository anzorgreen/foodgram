import base64

from django.core.files.base import ContentFile
from rest_framework import serializers
from users.models import Favorite
from users.serializers import UserListSerializer

from backend.settings import MIN_COOKING_TIME

from .models import Cart, Ingredient, Recipe, RecipeIngredient, Tag


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для количества ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        write_only=True,
        required=True,
        pk_field=serializers.IntegerField(),
        error_messages={
            "does_not_exist": "Ингредиент с id={pk_value} не существует.",
            "incorrect_type": "Некорректный тип данных для ID ингредиента."
        }
    )
    amount = serializers.IntegerField(
        required=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class Base64ImageField(serializers.ImageField):
    """Сериализатор для изображения в формате Base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления рецепта."""

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    ingredients = RecipeIngredientWriteSerializer(
        required=True,
        many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        pk_field=serializers.IntegerField(),
        error_messages={
            "does_not_exist": "Тега с id={pk_value} не существует.",
            "incorrect_type": "Некорректный тип данных для ID тега."
        }
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'tags', 'ingredients', 'name', 'image',
            'text', 'cooking_time', 'author'
        )

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами."""
        tags = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self._handle_tags_and_ingredients(recipe, tags, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами."""
        tag_ids = self.initial_data.pop('tags', [])
        new_tags = Tag.objects.filter(id__in=tag_ids)
        ingredients_data = validated_data.pop('ingredients', None)

        self._handle_tags_and_ingredients(instance, new_tags, ingredients_data)
        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def _handle_tags_and_ingredients(self, recipe,
                                     tags_data, ingredients_data):
        """Обработка тегов и ингредиентов для рецепта."""
        if tags_data:
            recipe.tags.clear()
            recipe.tags.set(tags_data)
        if ingredients_data:
            RecipeIngredient.objects.filter(recipe=recipe).delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
                for ingredient_data in ingredients_data
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data

    def validate(self, attrs):
        if self.partial:
            if 'ingredients' not in attrs:
                raise serializers.ValidationError(
                    'Необходимо указать ингредиенты')
            if 'tags' not in attrs:
                raise serializers.ValidationError(
                    'Необходимо указать хотя бы один тег'
                )
        return attrs

    def validate_name(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            queryset = Recipe.objects.filter(author=request.user, name=value)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    'У вас уже есть рецепт с таким названием.'
                )
        return value

    def validate_text(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле 'text' обязательно для заполнения."
            )
        return value

    def validate_ingredients(self, value):
        ingredients = []
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты'
            )
        for ingredient in value:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Неправильно указано количество'
                )
            if ingredient['id'] in ingredients:
                raise serializers.ValidationError(
                    'Не стоит указывать один ингредиент дважды'
                )
            ingredients.append(ingredient['id'])
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать хотя бы одни тег'
            )
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                'Не стоит указывать один тег дважды'
            )
        return value

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f'Время не может быть меньше {MIN_COOKING_TIME} мин.'
            )
        return value


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта."""

    author = UserListSerializer(many=False, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientWriteSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    def to_representation(self, instance):
        """Представление данных рецепта."""
        representation = super().to_representation(instance)
        ingredients = RecipeIngredient.objects.filter(recipe=instance)
        tags = instance.tags.all()
        representation['ingredients'] = [
            {
                'id': item.ingredient.id,
                'name': item.ingredient.name,
                'measurement_unit': item.ingredient.measurement_unit,
                'amount': item.amount
            } for item in ingredients
        ]
        representation['tags'] = []
        for tag in tags:
            representation['tags'].append(
                {'id': tag.id, 'name': tag.name, 'slug': tag.slug}
            )
        return representation

    def get_is_favorited(self, obj):
        """Проверка на добавление рецепта в избранное."""
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return obj.favorited_by.filter(user=request.user).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверка на добавление рецепта в корзину."""
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Cart.objects.filter(user=request.user, recipes=obj).exists()

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart',
            'name', 'image', 'text', 'cooking_time',
        )


class RecipeBriefSerializer(serializers.ModelSerializer):
    """Сериализатор с кратким описанием рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для управления корзиной пользователя."""

    recipe_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Cart
        fields = ('recipe_id',)

    def validate_recipe_id(self, value):
        """Проверяет, что рецепт с указанным ID существует."""
        if not Recipe.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Рецепт с указанным ID не существует.'
            )
        return value

    def add_recipe(self, user, recipe):
        """Добавляет рецепт в корзину пользователя."""
        cart, created = Cart.objects.get_or_create(user=user)
        if cart.recipes.filter(id=recipe.id).exists():
            raise serializers.ValidationError(
                'Рецепт уже в корзине.'
            )
        cart.recipes.add(recipe)
        return cart

    def remove_recipe(self, user, recipe):
        """Удаляет рецепт из корзины пользователя."""
        cart = Cart.objects.filter(user=user).first()
        if not cart:
            raise serializers.ValidationError(
                'Корзина не найдена.'
            )
        if not cart.recipes.filter(id=recipe.id).exists():
            raise serializers.ValidationError(
                'Рецепт не найден в корзине.'
            )
        cart.recipes.remove(recipe)
        return cart


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для управления избранным пользователя."""

    recipe_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ('recipe_id',)

    def validate_recipe_id(self, value):
        """Проверяет, что рецепт с указанным ID существует."""
        if not Recipe.objects.filter(id=value).exists():
            raise serializers.ValidationError(
                'Рецепт с указанным ID не существует.'
            )
        return value

    def add_to_favorite(self, user, recipe):
        """Добавляет рецепт в избранное пользователя."""
        if Favorite.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        Favorite.objects.create(user=user, recipe=recipe)
        return recipe

    def remove_from_favorite(self, user, recipe):
        """Удаляет рецепт из избранного пользователя."""
        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            raise serializers.ValidationError(
                'Рецепт не найден в избранном.'
            )
        favorite.delete()
        return recipe
