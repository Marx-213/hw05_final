# hw05_final

# Социальная сеть для публикации личных дневников.

![Python](https://img.shields.io/badge/Python_3.7-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/django_2.2.9-%23092E20?style=for-the-badge&logo=django&logoColor=white)
### Описание
На сайте можно создать свою страницу и посмотреть все записи автора. Подключена база данных. Десять последних записей выводятся на главную страницу.
Присутствует админка и  управление объектами модели Post: можно публиковать записи или редактировать, а также удалять существующие.
Пользователи могут заходить на чужие страницы, подписываться на авторов и комментировать их записи, а ещё переходить на страницу любого сообщества, где отображаются десять последних публикаций из этой группы.

### Технологии
Python 3.7

Django 2.2.9
### Установка
Клонировать репозиторий и перейти в него в командной строке:
```
git clone https://github.com/yandex-praktikum/hw02_community.git
``` 
Установить и активировать виртуальное окружение:
``` 
python3 -m venv env
source env/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
pip install -r requirements.txt
``` 
Перейти в папку yatube, применить миграции и запустить сервер:
```
cd yatube
python manage.py migrate
python manage.py runserver
``` 
