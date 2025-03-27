import base64

from django.core.files.base import ContentFile
from rest_framework import serializers

from backend.settings import MIN_COOKING_TIME, MIN_INGREDIENT_AMOUNT
from .models import Cart, Favorite, Ingredient, Recipe, RecipeIngredient, Tag
from users.serializers import UserListSerializer


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


class RecipeIngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для количества ингредиентов."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
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
    name = serializers.SerializerMethodField(
        read_only=True
    )
    measurement_unit = serializers.SerializerMethodField(
        read_only=True
    )

    def get_name(self, obj):
        return obj.ingredient.name

    def get_measurement_unit(self, obj):
        return obj.ingredient.measurement_unit

    def valideate_amount(self, value):
        if value < MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError(
                'Неправильно указано количество'
            )
        return value

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount', 'name', 'measurement_unit')


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
    ingredients = RecipeIngredientSerializer(
        required=True,
        many=True)
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=True,
        pk_field=serializers.IntegerField(),
        error_messages={
            "does_not_exist": "Тега с id={pk_value} не существует.",
            "incorrect_type": "Некорректный тип данных для ID тега."
        }
    )
    text = serializers.CharField(
        required=True
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
        tags = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients', None)
        self._handle_tags_and_ingredients(instance, tags, ingredients_data)
        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def _handle_tags_and_ingredients(self, recipe,
                                     tags_data, ingredients_data):
        """Обработка тегов и ингредиентов для рецепта."""
        recipe.tags.clear()
        recipe.tags.set(tags_data)
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

    def validate_ingredients(self, value):
        ingredients = []
        if not value:
            raise serializers.ValidationError(
                'Необходимо указать ингредиенты'
            )
        for ingredient in value:
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
    ingredients = RecipeIngredientSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

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
        request = self.context.get('request')
        if request.method == 'POST':
            cart, _ = Cart.objects.get_or_create(user=request.user)
            if cart.recipes.filter(id=value).exists():
                raise serializers.ValidationError(
                    'Рецепт уже в корзине.'
                )
        elif request.method == 'DELETE':
            cart = Cart.objects.filter(user=request.user).first()
            if not cart or not cart.recipes.filter(id=value).exists():
                raise serializers.ValidationError(
                    'Рецепт не найден в корзине.'
                )
        return value


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
        request = self.context.get('request')
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe__id=value).exists():
                raise serializers.ValidationError(
                    'Рецепт уже добавлен в избранное.'
                )
        elif request.method == 'DELETE':
            if not Favorite.objects.filter(
                user=user,
                recipe__id=value
            ).exists():
                raise serializers.ValidationError(
                    'Рецепт не найден в избранном.'
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
