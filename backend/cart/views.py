from django.shortcuts import render
from collections import defaultdict

from models import Cart
# Create your views here.

def get_or_create_cart(user):
    # Попробуем найти корзину для текущего пользователя, если она существует
    cart, created = Cart.objects.get_or_create(user=user)
    return cart

