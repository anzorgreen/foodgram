from django.db import models
from users.models import BaseModel
from django.core.exceptions import ValidationError


class Cart(models.Model):
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
    created_at = models.DateTimeField


    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return (f'Корзина пользователя '
                f'{self.user.first_name} {self.user.last_name}')


class Subsrciption(BaseModel):

    subscriber = models.ForeignKey(
        'users.User',
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Подписчики',
    )
    subscribed_to = models.ForeignKey(
        'users.User',
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Подписан на:',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscribed_to'],
                name='unique_subscription')]

    def __str__(self):
        return f'{self.subscriber} подписан на {self.subscribed_to}'

    def clean(self):
        if self.subscriber == self.subscribed_to:
            raise ValidationError("Вы не можете подписываться на самого себя.")

    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)

class Favorite(BaseModel):

    recipe = models.ForeignKey(
        'recipes.Recipe',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепты',
    )
    user = models.ForeignKey(
        'users.User',
        blank=True,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='В избранных'
    )
    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'user'],
                name='unique_favorite')]

    def __str__(self):
        return f'{self.user} добавил {self.recipe} в избранное'
