from collections import defaultdict

from cart.models import Cart


def get_ingredients_from_cart(user):
    """Получает все ингредиенты из корзины пользователя."""
    try:
        cart = Cart.objects.get(user=user)
    except Cart.DoesNotExist:
        return []
    recipes_in_cart = cart.recipes.all()
    ingredients_dict = defaultdict(lambda: {'amount': 0, 'unit': ''})
    for recipe in recipes_in_cart:
        for recipe_ingredient in recipe.ingredients.all():
            ingredient = recipe_ingredient.ingredient
            ingredients_dict[ingredient.name][
                'amount'
            ] += recipe_ingredient.amount
            ingredients_dict[ingredient.name][
                'measurement_unit'
            ] = ingredient.measurement_unit
    return ingredients_dict
