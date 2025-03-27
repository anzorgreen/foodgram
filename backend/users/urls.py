from django.urls import include, path
from rest_framework import routers

from .views import CustomObtainAuthToken, UserView

router = routers.DefaultRouter()
router.register('users', UserView, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'auth/token/login/',
        CustomObtainAuthToken.as_view(),
        name='custom-token-login'
    ),
    path('users/', include('djoser.urls')),
]
