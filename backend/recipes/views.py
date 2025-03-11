from collections import defaultdict
from io import StringIO

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import (DjangoFilterBackend,
                                           FilterSet,
                                           CharFilter)
from django_filters import rest_framework as filters
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view
from .models import Ingredient, Recipe, Tag
from cart.models import Cart, Favorite
from .serializers import (RecipeFullSerializer,
                          TagSerializer,
                          IngredientSerializer,
                          RecipeBriefSerializer)
from .permissions import IsOwnerOrReadOnly, IsAdmin
from pagination import CustomPageNumberPagination

class RecipeFilter(FilterSet):
    author_first_name = filters.CharFilter(field_name='author__first_name', lookup_expr='icontains')
    author = filters.NumberFilter(field_name='author__id')
    is_favorited = filters.BooleanFilter(method='filter_is_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_is_in_shopping_cart')
    tags = filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        queryset=Tag.objects.all(),
        to_field_name='slug',
    )
    class Meta:
        model = Recipe
        fields = (
            'author',
            'author_first_name',
            'is_favorited',
            'is_in_shopping_cart',
            'tags',
        )
    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.all()
        if value:
            return queryset.filter(favorites__user=user)
        return queryset.exclude(favorites__user=user)
    
    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.all()
        if value:
            return queryset.filter(carts__user=user)
        return queryset.exclude(carts__user=user)

def get_ingredients_from_cart(user):
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        return []
    recipes_in_cart = cart.recipes.all()
    ingredients_dict = defaultdict(lambda: {'amount': 0, 'unit': ''})
    for recipe in recipes_in_cart:
        for recipe_ingredient in recipe.ingredients.all():
            ingredient = recipe_ingredient.ingredient
            ingredients_dict[ingredient.name]['amount'] += recipe_ingredient.amount
            ingredients_dict[ingredient.name]['measurement_unit'] = ingredient.measurement_unit
    return ingredients_dict


class RecipeView(viewsets.ModelViewSet):
    serializer_class = RecipeFullSerializer
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'recipe_by_link'):
            return (AllowAny(),)
        elif self.action in ('update', 'partial_update', 'destroy',):
            return (IsOwnerOrReadOnly(),)
        return (IsAuthenticated(),)
    
    def get_serializer_class(self):
        if self.action == 'favorite':
            return RecipeBriefSerializer
        return super().get_serializer_class()


    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def manage_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        cart, created = Cart.objects.get_or_create(user=user)
        recipes_in_cart = cart.recipes.all()
        if request.method == 'POST':
            if recipe in recipes_in_cart:
                return Response(
                    {'detail': 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart.recipes.add(recipe)
            serializer = RecipeBriefSerializer(
                recipe,
                many=False,
                context={
                    'request': request
                })
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if recipe not in recipes_in_cart:
                return Response(
                    {'detail': 'Такого рецепта не было в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            cart.recipes.remove(recipe)
            return Response(
                {'detail': 'Рецепт успешно удалён из корзины.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        ingredients = get_ingredients_from_cart(request.user)
        output = StringIO()
        for name, data in ingredients.items():
            output.write(f"{name} ({data['measurement_unit']}) ― {int(data['amount'])}\n")
        response = HttpResponse(
            output.getvalue(),
            content_type='text/plain'
        )
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = self.get_serializer(recipe)
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {'detail': 'Рецепта нет в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(
                {'detail': 'Рецепт удалён из избранного.'},
                status=status.HTTP_204_NO_CONTENT
            )

    @action(detail=True, methods=['get'], url_path='get-link')
    def recipe_by_link(self, request, pk=None):
        short_link = get_object_or_404(Recipe, id=pk).generate_short_url()
        return Response(
            {"short-link": short_link}
        )


@api_view(['GET'])
def recipe_by_short_url(request, short_url):
    recipe = get_object_or_404(Recipe, short_url=short_url)
    serializer = RecipeFullSerializer(recipe, context={'request': request})
    return Response(serializer.data)

class TagView(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get', 'head', 'options']


class IngredientFilter(FilterSet):
    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = (
            'name',
        )


class IngredientView(viewsets.ModelViewSet):
    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get', 'head', 'options']
