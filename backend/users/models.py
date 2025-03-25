from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from rest_framework.authentication import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


class User(AbstractUser):
    """
    Кастомная модель пользователя с дополнительным полем аватара.

    Используется email в качестве поля для аутентификации.
    """

    avatar = models.ImageField(
        blank=True,
        null=True,
        verbose_name='Изображение',
        upload_to='users/images/'
    )
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True)
    REQUIRED_FIELDS = ('username',)
    USERNAME_FIELD = 'email'

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    def clean(self):
        if not self.first_name:
            raise ValidationError(
                'Введите имя'
            )
        elif not self.last_name:
            raise ValidationError(
                'Введите фамилию'
            )
        super().clean()


class CustomObtainAuthToken(ObtainAuthToken):
    """Кастомный класс для аутентификации через email и пароль."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        """Обработка POST-запроса для аутентификации и создания токена."""
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(request, username=email, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response({'detail': 'Invalid credentials'}, status=400)


class BaseModel(models.Model):
    """Абстрактная модель с полями времени создания и обновления."""

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления')

    class Meta:
        abstract = True


class Subscription(BaseModel):
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
        return f'{self.subscriber} подписан на {self.subscribed_to}'

    def clean(self):
        """Проверка, чтобы пользователь не мог подписаться на самого себя."""
        if self.subscriber == self.subscribed_to:
            raise ValidationError(
                "Вы не можете подписываться на самого себя."
            )

    def save(self, *args, **kwargs):
        """Переопределённый метод сохранения с вызовом full_clean."""
        self.full_clean()
        super().save(*args, **kwargs)


class Favorite(BaseModel):
    """Модель избранных рецептов."""

    recipe = models.ForeignKey(
        'recipes.Recipe',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Рецепты',
    )
    user = models.ForeignKey(
        'User',
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

    def clean(self):
        super().clean()
        if Favorite.objects.filter(
            user=self.user,
            recipe=self.recipe
        ).exclude(pk=self.pk).exists():
            raise ValidationError(
                "Этот рецепт уже добавлен в избранное."
            )
