# Проект Foodgram
Ссылка на проект:
http://foodgramproject.sytes.net
Это веб-приложение, где вы можете делиться своими любимыми рецептами, а также находить рецепты других пользователей

[![Main Foodgram workflow](https://github.com/anzorgreen/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/anzorgreen/foodgram/actions/workflows/main.yml)

## Установка Docker
Этот проект работает в контейнерах Docker, поэтому вам нужно установить Docker на вашем ПК или удалённом сервере.

Для Linux:

```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin
```
Или скачайте Docker Desktop с официального сайта Docker https://www.docker.com/products/docker-desktop и следуйте инструкциям по установке.

## Развёртывание на удалённом сервере
Перенесите файл docker-compose.production.yml на сервер любым удобным способом.
Затем скачайте и запустите образы Docker командой:
```
sudo docker compose -f docker-compose.production.yml up -d
```
Выполните миграции и соберите статические файлы:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
Проект будет доступен по IP-адресу вашего сервера.

## Локальная разработка
Клонируйте репозиторий на свой компьютер:
```
git clone git@github.com:anzorgreen/foodgram.git
```
Для отладки используйте файл docker-compose.yml вместо docker-compose.production.yml, чтобы собирать образы из локальных файлов:
```
docker compose up -d
```
Выполните миграции и соберите статические файлы:
```
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
Проект будет доступен локально по адресу http://localhost:9000/.
```

## Использованные технологии
Django
Nginx
Gunicorn
React
Docker

## Автор
Анзор Квачантирадзе
Email: anzor.green@gmail.com
