@echo off
python manage.py collectstatic --noinput
python manage.py runserver
pause
