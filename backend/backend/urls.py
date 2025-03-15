from django.contrib import admin
from django.urls import path, include
from rest_framework import routers

from recipes.views import (
    RecipeView, TagView, IngredientView, recipe_by_short_url
)
from users.models import CustomObtainAuthToken
from users.views import UserView

router = routers.DefaultRouter()
router.register('recipes', RecipeView, basename='recipe')
router.register('tags', TagView, basename='tag')
router.register('ingredients', IngredientView, basename='ingredient')
router.register('users', UserView, basename='user')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/users/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path(
        'api/auth/token/login/',
        CustomObtainAuthToken.as_view(),
        name='custom-token-login'
    ),
    path(
        '<uuid:short_url>/',
        recipe_by_short_url,
        name='recipe-short-url'
    ),
]
