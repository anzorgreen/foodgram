from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import tempfile
from .models import Recipe, Tag, Ingredient, RecipeIngredient
from cart.models import Favorite, Cart
from users.serializers import UserListSerializer
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator
from django.core.validators import MinValueValidator, MaxLengthValidator

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
            'slug',
        )

class TagWriteSerializer(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        return Tag.objects.all()

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )
class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class RecipeFullSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        required=True,
        validators=[MaxLengthValidator(256)],
        error_messages={'details': 'Название не должно превышать 256 символов'}
    )
    ingredients = IngredientAmountSerializer(
        many=True,
        required=True,
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    author = UserListSerializer(
        many=False,
        read_only=True
    )
    is_favorited = serializers.SerializerMethodField(
        read_only=True
    )
    is_in_shopping_cart = serializers.SerializerMethodField(
        read_only=True
    )
    image = Base64ImageField(
        required=True, allow_null=False
    )
    cooking_time = serializers.IntegerField(
        validators=[MinValueValidator(1)],
        error_messages={'details': 'Время не может быть меньше одной минуты'}
    )

    def create(self, validated_data):
        request = self.context.get('request')
        tags = validated_data.pop('tags', [])
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data, author=request.user)
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
        recipe.tags.set(tags)
        return recipe

    def update(self, instance, validated_data):
        required_fields = (
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
        )
        for field in required_fields:
            if field not in validated_data:
                raise serializers.ValidationError(f'Отсутстует поле {field}')
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        tag_ids = self.initial_data.pop('tags', [])
        instance.tags.clear()
        new_tags = [Tag.objects.get(id=tag_id) for tag_id in tag_ids]
        instance.tags.set(new_tags)
        ingredients_data = validated_data.pop('ingredients')
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
        instance.save()
        return instance

    def to_representation(self, instance):
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
        representation['tags'] = [
                {'id': item.id,
                 'name': item.name,
                 'slug': item.slug} for item in tags
        ]
        return representation

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Favorite.objects.filter(
            user=request.user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request.user.is_authenticated:
            return False
        return Cart.objects.filter(user=request.user, recipes=obj).exists()

    def validate_name(self, value):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            instance = self.instance
            if instance:
                if Recipe.objects.filter(author=request.user, name=value).exclude(id=instance.id).exists():
                    raise serializers.ValidationError('У вас уже есть рецепт с таким названием.')
            else:
                if Recipe.objects.filter(author=request.user, name=value).exists():
                    raise serializers.ValidationError('У вас уже есть рецепт с таким названием.')
        return value

    def validate_ingredients(self, value):
        ids = []
        if not value:
            raise serializers.ValidationError('Необходимо указать ингредиенты')
        for ingredient in value:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise serializers.ValidationError('Убедитесь, что все ингредиенты есть в базе данных')
            if float(ingredient['amount']) <= 0:
                raise serializers.ValidationError('Неправильно указано количество')
            if ingredient['id'] in ids:
                raise serializers.ValidationError('Не стоит указывать один ингредиент дважды')
            ids.append(ingredient['id'])
        return value
    
    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Необходимо указать тег')
        tag_ids = [tag.id for tag in value]
        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Не стоит указывать один тег дважды')
        existing_tags = Tag.objects.filter(id__in=tag_ids)
        if len(existing_tags) != len(value):
            raise serializers.ValidationError('Указанного тега нет в базе')
        return value
    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

class RecipeBriefSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )
        read_only_fields = (
            'id',
            'name',
            'image',
            'cooking_time',
        )