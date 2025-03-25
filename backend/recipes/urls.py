from django.urls import include, path
from rest_framework import routers

from .views import IngredientView, RecipeView, TagView, recipe_by_short_url

router = routers.DefaultRouter()
router.register('recipes', RecipeView, basename='recipe')
router.register('tags', TagView, basename='tag')
router.register('ingredients', IngredientView, basename='ingredient')

urlpatterns = [
    path('', include(router.urls)),
    path('<uuid:short_url>/', recipe_by_short_url, name='recipe-short-url'),
]
