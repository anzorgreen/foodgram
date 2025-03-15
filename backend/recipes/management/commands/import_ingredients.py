import csv
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов в базу данных."""

    help = "Импорт ингредиентов из CSV-файла"

    def handle(self, *args, **kwargs):
        file_path = "recipes/fixtures/ingredients.csv"
        with open(file_path, encoding="utf-8") as file:
            reader = csv.DictReader(file)
            ingredients = [
                Ingredient(
                    name=row["name"],
                    measurement_unit=row["measurement_unit"])
                for row in reader
            ]
            Ingredient.objects.bulk_create(ingredients)
        self.stdout.write(self.style.SUCCESS("Ингредиенты успешно загружены!"))
