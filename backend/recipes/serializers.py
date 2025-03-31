import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
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


class RecipeIngredientWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для создания/обновления ингредиентов в рецепте."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        required=True,
        pk_field=serializers.IntegerField(),
        error_messages={
            'does_not_exist': 'Ингредиент с id={pk_value} не существует.',
            'incorrect_type': 'Некорректный тип данных для ID ингредиента.'
        }
    )
    amount = serializers.IntegerField(required=True)

    def validate_amount(self, value):
        if value < MIN_INGREDIENT_AMOUNT:
            raise serializers.ValidationError('Неправильно указано количество')
        return value

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для представления ингредиентов рецепта."""
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    amount = serializers.IntegerField(read_only=True)
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True)

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
    ingredients = RecipeIngredientWriteSerializer(
        required=True,
        many=True
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        write_only=True,
        required=True,
        pk_field=serializers.IntegerField(),
        error_messages={
            'does_not_exist': 'Тега с id={pk_value} не существует.',
            'incorrect_type': 'Некорректный тип данных для ID тега.'
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
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._handle_ingredients(recipe, ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами."""
        instance.tags.clear()
        instance.tags.set(validated_data.pop('tags'))
        self._handle_ingredients(instance, validated_data.pop('ingredients'))
        instance = super().update(instance, validated_data)
        instance.save()
        return instance

    def _handle_ingredients(self, recipe, ingredients_data):
        """Обработка ингредиентов для рецепта."""
        recipe.ingredients.all().delete()
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
            queryset = request.user.recipes.filter(name=value)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)
            if queryset.exists():
                raise serializers.ValidationError(
                    'У вас уже есть рецепт с таким названием.'
                )
        return value

    def validate_cooking_time(self, value):
        if value < MIN_COOKING_TIME:
            raise serializers.ValidationError(
                f'Время не может быть меньше {MIN_COOKING_TIME} мин.'
            )
        return value

    def validate(self, attrs):
        """Валидация полей `tags` и `ingredients`."""
        if 'tags' not in attrs or not attrs['tags']:
            raise serializers.ValidationError(
                {'tags': 'Необходимо указать хотя бы один тег.'}
            )
        if 'ingredients' not in attrs or not attrs['ingredients']:
            raise serializers.ValidationError(
                {'ingredients': 'Необходимо указать хотя бы один ингредиент.'}
            )
        tag_ids = [tag.id for tag in attrs['tags']]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError(
                {'tags': 'Не стоит указывать один тег дважды.'}
            )
        ingredient_ids = set()
        for ingredient in attrs['ingredients']:
            if ingredient['id'] in ingredient_ids:
                raise serializers.ValidationError(
                    {
                        'ingredients':
                        'Не стоит указывать один ингредиент дважды.'
                    }
                )
            ingredient_ids.add(ingredient['id'])
        return attrs


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения рецепта."""

    author = UserListSerializer(many=False, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    ingredients = RecipeIngredientReadSerializer(many=True, read_only=True)
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
        if hasattr(request.user, 'cart'):
            return request.user.cart.recipes.filter(pk=obj.pk).exists()
        return False

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
        request = self.context.get('request')
        try:
            cart = request.user.cart
        except Cart.DoesNotExist:
            cart = None
        if request.method == 'POST':
            if cart and cart.recipes.filter(id=value).exists():
                raise serializers.ValidationError(
                    'Рецепт уже в корзине.'
                )
        else:
            if not cart or not cart.recipes.filter(id=value).exists():
                raise serializers.ValidationError(
                    'Рецепт не найден в корзине.'
                )
        return value

    def create(self, validated_data):
        """Создаёт корзину, если её нет."""
        user = self.context['request'].user
        recipe = get_object_or_404(Recipe, pk=validated_data['recipe_id'])
        Cart.objects.get_or_create(user=user)
        return recipe

    def to_representation(self, instance):
        """Возвращает краткую информацию о рецепте."""
        return RecipeBriefSerializer(instance, context=self.context).data


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для управления избранным пользователя."""

    recipe_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Favorite
        fields = ('recipe_id',)

    def validate_recipe_id(self, value):
        request = self.context.get('request')
        if request.method == 'POST' and request.user.favorites.filter(
            recipe_id=value
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное.'
            )
        if request.method == 'DELETE' and not request.user.favorites.filter(
            recipe_id=value
        ).exists():
            raise serializers.ValidationError(
                'Рецепт не найден в избранном.'
            )
        return value

    def to_representation(self, instance):
        """Возвращает краткую информацию о рецепте."""
        return RecipeBriefSerializer(instance, context=self.context).data
