from django.contrib import admin

from .models import Cart
from recipes.models import Recipe


class RecipeInline(admin.TabularInline):
    """Inline-добавление рецептов в корзину."""

    model = Recipe
    extra = 1
    fields = (
        'name',
        'description',
        'author',
    )


class CartAdmin(admin.ModelAdmin):
    """Отображение корзин пользователей в админке."""

    list_display = (
        'user',
        'created_at',
    )
    inlines = (RecipeInline,)


admin.site.register(Cart)
