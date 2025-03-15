from django.db import models


class Cart(models.Model):
    """
    Модель корзины пользователя, связывающая пользователя с рецептами.

    Создаётся при первом добавлении рецепта в корзину.
    """

    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='cart',
        verbose_name='Пользователь'
    )
    recipes = models.ManyToManyField(
        'recipes.Recipe',
        related_name='carts',
        verbose_name='Рецепт')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return (f'Корзина пользователя '
                f'{self.user.first_name} {self.user.last_name}'
                f' ({self.user.username})')
