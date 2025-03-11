from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from cart.models import Favorite, Cart, Subsrciption






class FavouriteInline(admin.TabularInline):
    model = Favorite


class CartInline(admin.TabularInline):
    model = Cart


class SubscrebersInline(admin.TabularInline):
    model = Subsrciption
    fk_name = 'subscriber'

class SubsrciptionsInline(admin.TabularInline):
    model = Subsrciption
    fk_name = 'subscribed_to'

class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Персональные данные', {'fields': ('first_name', 'last_name', 'avatar')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    search_fields = (
        'email',
        'username',
    )
    list_display = (
        'id',
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'avatar'
    )
    ordering = (
        'id',
    )
    inlines = (FavouriteInline,
               CartInline,
               SubsrciptionsInline,
               SubscrebersInline,
               )

admin.site.register(User, CustomUserAdmin)
admin.site.register(Subsrciption)