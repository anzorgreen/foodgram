from django.db.models import Sum

from .models import Cart, RecipeIngredient


def get_ingredients_from_cart(user):
    """Получает все ингредиенты из корзины пользователя."""
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        return {}
    ingredients = (
        RecipeIngredient.objects
        .filter(recipe__carts=cart)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
    )
    ingredients_dict = {
        item['ingredient__name']: {
            'amount': item['total_amount'],
            'measurement_unit': item['ingredient__measurement_unit']
        }
        for item in ingredients
    }
    return ingredients_dict
