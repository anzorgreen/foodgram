# Generated by Django 5.1.4 on 2025-03-11 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cart', '0001_initial'),
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='recipes',
            field=models.ManyToManyField(related_name='carts', to='recipes.recipe', verbose_name='Рецепт'),
        ),
    ]
