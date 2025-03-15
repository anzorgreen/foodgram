from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from cart.models import Cart
from .models import Favorite, Subscription


class FavouriteInline(admin.TabularInline):
    """Inline-добавление избранных рецептов."""

    model = Favorite


class CartInline(admin.TabularInline):
    """Inline-добавление карзины."""

    model = Cart


class SubscribersInline(admin.TabularInline):
    """Inline-добавление подписчиков пользователя."""

    model = Subscription
    fk_name = 'subscriber'


class SubscriptionsInline(admin.TabularInline):
    """Inline-добавление подписок текущего пользователя."""

    model = Subscription
    fk_name = 'subscribed_to'


class CustomUserAdmin(UserAdmin):
    """Отображение модели пользователя в админке."""

    fieldsets = (
        (
            None,
            {'fields': ('username', 'email', 'password')}
        ),
        (
            'Персональные данные',
            {'fields': ('first_name', 'last_name', 'avatar')}
        ),
        (
            'Разрешения',
            {'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )}
        ),
        (
            'Важные даты', {'fields': ('last_login', 'date_joined')}
        ),
    )
    search_fields = ('email', 'username')
    list_display = (
        'id', 'username', 'email', 'first_name',
        'last_name', 'is_staff', 'avatar',
    )
    ordering = ('id',)
    inlines = (
        FavouriteInline, CartInline,
        SubscriptionsInline, SubscribersInline,
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Subscription)
admin.site.register(Favorite)
