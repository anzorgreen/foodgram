import csv
from django.core.management.base import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):

    help = 'Load tags from CSV'

    def handle(self, *args, **kwargs):
        with open('recipes/fixtures/tags.csv', 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for name, slug in reader:
                Tag.objects.get_or_create(name=name.strip(), slug=slug.strip())
        self.stdout.write(self.style.SUCCESS('Теги загружены!'))
