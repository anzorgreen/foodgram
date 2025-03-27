import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
from users.models import BaseModel

from backend.settings import (MAX_LENGTH_NAME, MAX_LENGTH_SHORT_DESCRIPTION,
                              MAX_LENGTH_SLUG, MIN_COOKING_TIME,
                              MIN_IMAGE_SIZE_MB, MIN_INGREDIENT_AMOUNT)


class Recipe(BaseModel):
    """Модель рецепта."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        blank=False,
        null=False,
        verbose_name='Название',
        unique=True
    )
    text = models.TextField(
        blank=False,
        null=False,
        verbose_name='Описание'
    )
    image = models.ImageField(
        default=None,
        blank=False,
        verbose_name='Изображение',
        upload_to='recipes/images/'
    )
    cooking_time = models.IntegerField(
        blank=False,
        null=False,
        verbose_name='Время приготовления',
    )
    author = models.ForeignKey(
        'users.User',
        blank=False,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    tags = models.ManyToManyField(
        'recipes.Tag',
        blank=False,
        related_name='recipes',
        verbose_name='Тег'
    )
    short_url = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_author'
            )
        ]

    def __str__(self):
        return f'{self.name} (Автор: {self.author})'

    def generate_short_url(self):
        """Генерация короткого URL на основе домена."""
        domain = settings.SITE_DOMAIN
        return f'{domain}/{self.short_url}'

    def clean(self):
        """Проверка изображения и наличия ингредиентов перед сохранением."""
        if self.image and self.image.size > MIN_IMAGE_SIZE_MB * 1024 * 1024:
            raise ValidationError(
                f'Размер изображения не должен превышать '
                f'{MIN_IMAGE_SIZE_MB} МБ'
            )
        if self.pk and not self.ingredients.exists():
            raise ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.'
            )
        if self.cooking_time < MIN_COOKING_TIME:
            raise ValidationError(
                f'Поле "cooking_time" ожидает число'
                f' большее или равное {MIN_COOKING_TIME}'
            )
        super().clean()

    def short_description(self):
        """Получение короткого описания рецепта."""
        return ((self.text[MAX_LENGTH_SHORT_DESCRIPTION] + '...') if self.text
                else 'Описание отсутствует')


@receiver(post_delete, sender=Recipe)
def delete_recipe_image(sender, instance, **kwargs):
    """Удаляет файл изображения при удалении рецепта."""
    if instance.image:
        if os.path.isfile(instance.image.path):
            os.remove(instance.image.path)


class Tag(BaseModel):
    """Модель тега для категоризации рецептов."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        blank=False,
        null=False,
        unique=True,
        verbose_name='Название тега'
    )
    slug = models.SlugField(
        max_length=MAX_LENGTH_SLUG,
        blank=False,
        null=False,
        unique=True,
        verbose_name='Слаг'
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name}/{self.slug}'


class Ingredient(BaseModel):
    """Модель ингредиента с названием и единицей измерения."""

    name = models.CharField(
        max_length=MAX_LENGTH_NAME,
        blank=False,
        null=False,
        unique=True,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGTH_SLUG,
        blank=False,
        null=False,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'measurement_unit'],
                name='unique_ingredient')
        ]

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class RecipeIngredient(models.Model):
    """Связь рецепта с ингредиентом и его количеством."""

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='ingredients',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Ингредиент'
    )
    amount = models.IntegerField(
        verbose_name='Количество'
    )

    class Meta:
        verbose_name = 'Связь рецепт - ингредиент'
        verbose_name_plural = 'Связи рецепт - ингредиенты'
        ordering = ('recipe__name',)

    def clean(self):
        if self.amount < MIN_INGREDIENT_AMOUNT:
            raise ValidationError(
                f'Поле "amount" ожидает число '
                f'большее или равное {MIN_INGREDIENT_AMOUNT}'
            )
        super().clean()

    def __str__(self):
        return (
            f'{self.amount} {self.ingredient.measurement_unit} '
            f'{self.ingredient.name} для {self.recipe.name}'
        )


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
        'Recipe',
        related_name='carts',
        verbose_name='Рецепт',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

    def __str__(self):
        return (f'Корзина пользователя '
                f'{self.user.first_name} {self.user.last_name}'
                f' ({self.user.username})')


class Favorite(BaseModel):
    """Модель избранных рецептов."""

    recipe = models.ForeignKey(
        'Recipe',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='favorited_by',
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
