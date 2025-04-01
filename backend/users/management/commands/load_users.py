import csv

from django.core.management.base import BaseCommand

from users.models import User


class Command(BaseCommand):
    """Команда для загрузки тестовых пользователей."""

    help = 'Load test users from CSV file'

    def handle(self, *args, **options):
        csv_file = 'users/fixtures/users.csv'
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                user = User(
                    email=row['email'],
                    username=row['username'],
                    first_name=row['first_name'],
                    last_name=row['last_name']
                )
                user.set_password(row['password'])
                user.save()
        self.stdout.write(self.style.SUCCESS('Пользователи успешно загружены'))
