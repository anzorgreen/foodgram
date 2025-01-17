from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import tempfile
from .models import Recipe, Tag, Ingredient, RecipeIngredient
from cart.models import Favorite, Cart
from users.serializers import UserListSerializer


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = (
            'id',
            'name',
        )

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = (
            'id',
            'name',
            'measurement_unit',
        )

class IngredientAmountSerializer(serializers.Serializer):
    id = serializers.IntegerField() # Ingreients id
    amount = serializers.IntegerField() # Amount of ingredient

class TagInRecipeSerializer(serializers.Serializer):
    id = serializers.IntegerField()

    # def get_id(self, obj):
    #     ingredients = 'AAAAAAA'
    #     amounts = 'Bbbbbbbbb'

            # Прописать возврат (id, name, unit, amount)
    # def get_amount(self, obj):


    # class Meta:
    #     model = RecipeIngredient
    #     fields = ('ingredients', 'amount',)

class RecipeFullSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(
        many=True
    )
    tags = TagSerializer(
        many=True, read_only=True
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
    short_url = serializers.SerializerMethodField(
        read_only=True
    )
    image = serializers.CharField()

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        request = self.context.get('request')
        image_base64 = validated_data.pop('image')
        format, img_str = image_base64.split(';base64,')
        extention = format.split('/')[1]
        image_data = base64.b64decode(img_str)
        temp_file = tempfile.NamedTemporaryFile(delete=True)
        temp_file.write(image_data)
        temp_file.flush()
        image_content = ContentFile(image_data, name=f'{validated_data["name"]}.{extention}')
        recipe = Recipe.objects.create(**validated_data, author=request.user, image=image_content)
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(id=ingredient_data['id'])
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )

        tag_ids = self.initial_data.pop('tags', [])
        new_tags = [Tag.objects.get(id=tag_id) for tag_id in tag_ids]
        recipe.tags.set(new_tags)
        recipe.tags.set(tag_ids)

        return recipe
    def update(self, instance, validated_data):
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
        if Cart.objects.filter(user=request.user).exists():
            return obj in Cart.objects.get(user=request.user).recipes.all()
        return False

    def get_short_url(self, obj):
        return obj.generate_short_url()

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
            'short_url',
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