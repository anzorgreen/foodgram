from django_filters import rest_framework as filters
from django_filters.rest_framework import CharFilter, FilterSet

from .models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    """
    Фильтр для ингредиентов.

    Позволяет фильтровать ингредиенты по имени.
    """

    name = CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(FilterSet):
    """
    Фильтр для рецептов.

    Позволяет фильтровать рецепты по автору, избранным, корзине и тегам.
    """

    author_first_name = filters.CharFilter(
        field_name='author__first_name',
        lookup_expr='icontains'
    )
    author = filters.NumberFilter(
        field_name='author__id'
    )
    is_favorited = filters.BooleanFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='filter_is_in_shopping_cart'
    )
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
        """Фильтрует рецепты по тому, добавлен ли рецепт в избранное."""
        user = self.request.user
        if not user.is_authenticated:
            return queryset.all()
        if value:
            return queryset.filter(favorited_by__user=user)
        return queryset.exclude(favorited_by__user=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтрует рецепты по тому, находятся ли они в корзине."""
        user = self.request.user
        if not user.is_authenticated:
            return queryset.all()
        if value:
            return queryset.filter(carts__user=user)
        return queryset.exclude(carts__user=user)
