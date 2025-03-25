from django.contrib import admin

from .models import Cart, Ingredient, Recipe, RecipeIngredient, Tag


class RecipeIngredientInline(admin.TabularInline):
    """Inline-добавление ингредиентов в рецепт."""

    model = RecipeIngredient
    extra = 1
    fields = (
        'ingredient',
        'amount',
    )


class RecipeAdmin(admin.ModelAdmin):
    """Отображение рецептов в админке."""

    search_fields = (
        'name',
        'author__first_name',
        'author__last_name',
    )
    list_filter = (
        'tags',
        'author__first_name',
    )
    list_display = (
        'id',
        'name',
        'author',
        'created_at',
        'updated_at',
    )
    inlines = (
        RecipeIngredientInline,
    )


class TagAdmin(admin.ModelAdmin):
    """Отображение тегов в админке."""

    list_display = (
        'name',
        'id',
        'slug',
        'created_at',
        'updated_at',
    )


class IngredientAdmin(admin.ModelAdmin):
    """Отображение ингредиентов в админке."""

    search_fields = (
        'name',
    )
    list_display = (
        'name',
        'measurement_unit',
    )


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
admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Ingredient, IngredientAdmin)
admin.site.register(Tag, TagAdmin)
