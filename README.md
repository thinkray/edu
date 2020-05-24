# Readme

------

## Introduction

This is a version of the project "One-to-one Online Tutoring Platform", which is under development.

In this version, we implemented following features:

1. Database structure
2. Registration
3. Login
4. Logout
5. Almost all of the APIs (except image upload) with permission check

In this version, we completed the design of following pages:

1. Home
2. Log in
3. Sign up

## Disclaimer of Warranty

THIS IS A PROGRAM WHICH IS UNDER DEVELOPMENT AND THERE IS NO WARRANTY FOR THE PROGRAM. 

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

To add a admin role to a user, you may use following command in `python manage.py shell`

    ```
	from django.contrib.auth.models import Group
	from account.models import User
    user = User.objects.get(pk=1) # Replace 1 with the user's id
    user.is_superuser = 1
	user.save()
    ```
	
To add a teacher role to a user, you may use following command in `python manage.py shell`

    ```
    # For the first time
    from django.contrib.auth.models import Group
	from account.models import User
    group = Group(name="Teacher")
    group.save()

    group = Group.objects.get(name="teacher")
    user = User.objects.get(pk=1) # Replace 1 with the user's id
    user.groups.add(group)
    ```