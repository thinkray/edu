# Readme

------

## Introduction

This is the final version of the project "One-to-one Online Tutoring Platform".

## Disclaimer of Warranty

THERE IS NO WARRANTY FOR THE PROGRAM. 

THE DEBUG MODE OF THE PROGRAM IS ON BY DEFAULT.

BY INSTALLING IT, YOU ACKNOWLEDGE THAT YOU ARE USING IT AT YOUR OWN RISK.

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

## Requirements

1. Python 3.6+
2. Django 3.0 See [How to install Django](https://docs.djangoproject.com/en/3.0/topics/install/) for details.
3. mysqlclient See [notes for the MySQL backend](https://docs.djangoproject.com/en/3.0/ref/databases/#mysql-notes) for details.

## Install & Run

1. Create a MySQL/MariaDB database and make sure you have a database user with full access of it.
2. Modify the database information in `edu/settings.py`.
3. Open a shell and change directory to the current directory.
4. Run the following command in your shell.

```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

5. Open your browser and go to the URL (e.g. http://127.0.0.1:8000/) which is in the command line output.

## User & User Group

Any user registered on the website is a student by default.

To add an admin role to a user, you may use following command in `python manage.py shell`

```
from django.contrib.auth.models import Group
from account.models import User
user = User.objects.get(pk=1) # Replace 1 with the user's id
user.is_superuser = 1
user.save()
```
	
To add a teacher role to a user, you can set it on `http://127.0.0.1:8000/dashboard/admin/user/` with an admin user.