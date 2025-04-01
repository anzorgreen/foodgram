from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models

from core.models import TimeStampModel
from backend.settings import MAX_LENTHG_SHORT_NAME


class User(AbstractUser):
    """
    Кастомная модель пользователя с дополнительным полем аватара.

    Используется email в качестве поля для аутентификации.
    """

    avatar = models.ImageField(
        blank=True,
        null=True,
        verbose_name='Изображение',
        upload_to='users/images/',
    )
    email = models.EmailField(
        unique=True,
        blank=False,
        verbose_name='Адрес электронной почты'
    )
    username = models.CharField(
        max_length=MAX_LENTHG_SHORT_NAME,
        unique=True,
        blank=False,
        verbose_name='Имя пользователя'
    )
    first_name = models.CharField(
        blank=False,
        max_length=MAX_LENTHG_SHORT_NAME,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        blank=False,
        max_length=MAX_LENTHG_SHORT_NAME,
        verbose_name='Фамилия'
    )
    REQUIRED_FIELDS = ('username',)
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Subscription(TimeStampModel):
    """Модель подписки."""

    subscriber = models.ForeignKey(
        'User',
        related_name='subscriptions',
        on_delete=models.CASCADE,
        verbose_name='Подписчики этого пользователя:',
    )
    subscribed_to = models.ForeignKey(
        'User',
        related_name='subscribers',
        on_delete=models.CASCADE,
        verbose_name='Этот пользователь подписан на:'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['subscriber', 'subscribed_to'],
                name='unique_subscription')]

    def __str__(self):
        return (
            f'{self.subscriber} ({self.subscriber.id}) '
            f'подписан на {self.subscribed_to} ({self.subscribed_to.id})'
        )

    def clean(self):
        """Проверка, чтобы пользователь не мог подписаться на самого себя."""
        if self.subscriber == self.subscribed_to:
            raise ValidationError(
                'Вы не можете подписываться на самого себя.'
            )

    def save(self, *args, **kwargs):
        """Переопределённый метод сохранения с вызовом full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)
