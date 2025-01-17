"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from rest_framework import routers
from django.urls import path, include
from recipes.views import RecipeView, TagView, IngredientView, recipe_by_short_url
from users.views import UserView
from users.models import CustomObtainAuthToken


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
    path('api/auth/token/login/', CustomObtainAuthToken.as_view(), name='custom-token-login'),
    path('<uuid:short_url>/', recipe_by_short_url, name='recipe-short-url'),
]

