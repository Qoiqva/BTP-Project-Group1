home page

http://127.0.0.1:8000/

---

admin page

http://127.0.0.1:8000/admin/

---

user credentials

username: greenpie
password: greenpie

---

admin credentials

username: greenpie_admin
password: btp405ncc

---

If you are on Windows, before running the app, please set the environment variable in bash terminal:

set DJANGO_SETTINGS_MODULE=greenpie.settings

---

to run the app :

python manage.py runserver

---

whenever you make changes to hte models, run the following commands to update in database:

first,

python manage.py makemigrations

then,

python manage.py migrate

---

P.S.

some dependencies in requirements.txt file are libraries from conda environment.
