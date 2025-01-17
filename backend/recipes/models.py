from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from constants import (MAX_LENGTH_TITLE, MAX_LENGTH_SLUG)
from users.models import BaseModel
import uuid
class Recipe(BaseModel):

    name = models.CharField(
        max_length=MAX_LENGTH_TITLE,
        blank=False,
        null=False,
        verbose_name='Название'
    )
    text = models.TextField(
        blank=False,
        null=False,
        verbose_name='Описание'
    )
    image = models.ImageField(
        blank=True,
        null=True,
        verbose_name='Изображение',
        upload_to='recipes/images/'
    )
    cooking_time = models.PositiveSmallIntegerField(
        blank=False,
        null=False,
        verbose_name='Время приготовления'
        )
    author = models.ForeignKey(
        'users.User',
        null=False,
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
        unique=True)

    class Meta:
        ordering = ['-created_at',]
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'author'],
                name='unique_name_author')]

    def generate_short_url(self):
        domain = settings.SITE_DOMAIN
        return f'{domain}/{self.short_url}'

    def __str__(self):
        return f'{self.name} (Автор: {self.author})'

    def short_description(self):
        return ((self.text[:25] + '...') if self.text
                else 'Описание отсутствует')

    def clean(self):
        if self.image and self.image.size > 5 * 1024 * 1024:
            raise ValidationError(
                'Размер изображения не должен превышать 5 МБ')
        super().clean()


class Tag(BaseModel):

    name = models.CharField(
        max_length=MAX_LENGTH_TITLE,
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

    name = models.CharField(
        max_length=MAX_LENGTH_TITLE,
        blank=False,
        null=False,
        unique=True,
        verbose_name='Ингредиент'
    )
    measurement_unit = models.CharField(
        max_length=50,
        blank=False,
        null=False,
        verbose_name='Единица измерения'
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'
 

class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='ingredients',
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipes',
    )
    amount = models.FloatField()

    def __str__(self):
        return (f'{self.amount} {self.ingredient.measurement_unit}'
                f'{self.ingredient.name} для {self.recipe.name}')
