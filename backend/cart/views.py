from models import Cart


def get_or_create_cart(user):
    """Создаёт модель корзины при попытке добавления в неё рецепта."""
    cart, created = Cart.objects.get_or_create(user=user)
    return cart
