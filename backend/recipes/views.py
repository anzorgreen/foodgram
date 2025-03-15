
from io import StringIO

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from cart.models import Cart
from .filters import RecipeFilter, IngredientFilter
from .models import Ingredient, Recipe, Tag
from utils.pagination import CustomPageNumberPagination
from .permissions import IsOwnerOrReadOnly
from .serializers import (RecipeFullSerializer,
                          TagSerializer,
                          IngredientSerializer,
                          RecipeBriefSerializer)
from users.models import Favorite
from .utils import get_ingredients_from_cart


class RecipeView(viewsets.ModelViewSet):
    """Представление для рецептов."""

    serializer_class = RecipeFullSerializer
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPageNumberPagination

    def get_permissions(self):
        """Возвращает права доступа в зависимости от действия."""
        if self.action in ('list', 'retrieve', 'recipe_by_link'):
            return (AllowAny(),)
        elif self.action in ('update', 'partial_update', 'destroy',):
            return (IsOwnerOrReadOnly(),)
        return (IsAuthenticated(),)

    def get_serializer_class(self):
        """Возвращает сериализатор в зависимости от действия."""
        if self.action == 'favorite':
            return RecipeBriefSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def manage_cart(self, request, pk=None):
        """Добавляет или удаляет рецепт из корзины пользователя."""
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
                context={'request': request}
            )
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
        """Генерирует короткую ссылку на рецепт."""
        short_link = get_object_or_404(Recipe, id=pk).generate_short_url()
        return Response(
            {"short-link": short_link}
        )


@api_view(['GET'])
def recipe_by_short_url(request, short_url):
    """Получает рецепт по короткой ссылке."""
    recipe = get_object_or_404(Recipe, short_url=short_url)
    serializer = RecipeFullSerializer(recipe, context={'request': request})
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
