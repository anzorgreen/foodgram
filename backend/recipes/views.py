from io import StringIO

from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from backend.pagination import CustomPageNumberPagination
from backend.permissions import IsOwnerOrReadOnly, StrictAuthenticated

from .filters import IngredientFilter, RecipeFilter
from .models import Ingredient, Recipe, Tag
from .serializers import (CartSerializer, FavoriteSerializer,
                          IngredientSerializer, RecipeBriefSerializer,
                          RecipeReadSerializer, RecipeWriteSerializer,
                          TagSerializer)
from .utils import get_ingredients_from_cart


class RecipeView(viewsets.ModelViewSet):
    """Представление для рецептов."""

    serializer_class = RecipeReadSerializer
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'recipe_by_link'):
            return (AllowAny(),)
        elif self.action in ('update', 'partial_update', 'destroy',):
            return (IsOwnerOrReadOnly(),)
        return (StrictAuthenticated(),)

    def get_serializer_class(self):
        if self.action == 'favorite':
            return RecipeBriefSerializer
        elif self.action in ('updata', 'partial_update', 'create', 'destroy'):
            return RecipeWriteSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def manage_cart(self, request, pk=None):
        """Добавить или удалить рецепт из корзины пользователя."""
        recipe = self.get_object()
        user = request.user
        cart_serializer = CartSerializer(
            data={'recipe_id': recipe.id},
            context={'request': request})

        if request.method == 'POST':
            try:
                cart_serializer.add_recipe(user, recipe)
                serializer = RecipeBriefSerializer(
                    recipe, context={'request': request}
                )
                return Response(
                    serializer.data,
                    status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        elif request.method == 'DELETE':
            try:
                cart_serializer.remove_recipe(user, recipe)
                return Response(
                    {'detail': 'Рецепт успешно удалён из корзины.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except ValidationError as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=False, methods=['get'], url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Скачать список ингредиентов из корзины."""
        ingredients = get_ingredients_from_cart(request.user)
        output = StringIO()
        for name, data in ingredients.items():
            output.write(
                f'{name} ({data["measurement_unit"]})'
                f' ― {int(data["amount"])}\n'
            )
        response = HttpResponse(
            output.getvalue(),
            content_type='text/plain'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        """Добавляет или удаляет рецепт из избранного пользователя."""
        recipe = get_object_or_404(Recipe, pk=pk)
        user = request.user
        favorite_serializer = FavoriteSerializer(
            data={'recipe_id': recipe.id},
            context={'request': request}
        )

        if request.method == 'POST':
            try:
                favorite_serializer.add_to_favorite(user, recipe)
                serializer = RecipeBriefSerializer(
                    recipe,
                    context={'request': request}
                )
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED
                )
            except ValidationError as e:
                return Response(
                    {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )

        elif request.method == 'DELETE':
            try:
                favorite_serializer.remove_from_favorite(user, recipe)
                return Response(
                    {'detail': 'Рецепт удалён из избранного.'},
                    status=status.HTTP_204_NO_CONTENT
                )
            except ValidationError as e:
                return Response(
                    {'detail': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

    @action(detail=True, methods=['get'], url_path='get-link')
    def recipe_by_link(self, request, pk=None):
        """Создать короткую ссылку на рецепт."""
        short_link = get_object_or_404(Recipe, id=pk).generate_short_url()
        return Response(
            {"short-link": short_link}
        )


@api_view(['GET'])
def recipe_by_short_url(request, short_url):
    """Получить рецепт по короткой ссылке."""
    recipe = get_object_or_404(Recipe, short_url=short_url)
    serializer = RecipeReadSerializer(recipe, context={'request': request})
    return Response(serializer.data)


class TagView(viewsets.ModelViewSet):
    """Представление для тегов."""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = [AllowAny]
    pagination_class = None
    http_method_names = ['get', 'head', 'options']


class IngredientView(viewsets.ModelViewSet):
    """Представление для ингредиентов."""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None
    http_method_names = ('get', 'head', 'options')
