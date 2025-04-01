import csv
import os

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Комманад для загрузки ингредиентов"""
    help = 'Load ingredients from CSV file into database'

    def handle(self, *args, **options):
        file_path = 'recipes/fixtures/ingredients.csv'
        full_path = os.path.join(
            os.path.dirname(__file__), '../../../', file_path
        )
        with open(full_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                name, unit = row
                Ingredient.objects.get_or_create(
                    name=name.strip(),
                    measurement_unit=unit.strip()
                )
        self.stdout.write(self.style.SUCCESS('Ингредиенты успешно загружены'))
