from django.db import models
from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.validators import ASCIIUsernameValidator
from django.core.validators import RegexValidator
from storage.models import BlobStorage

class UserManager(BaseUserManager):
    def create_user(self, username, password=None, name=None):
        """
        Creates and saves a User
        """
        # if not email:
        #     raise ValueError('Users must have an email address')

        self.model = User
        user = self.model(
            username=self.model.normalize_username(username),
            name=name,
            # email=self.normalize_email(email),
            # date_of_birth=date_of_birth,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, name=None):
        """
        Creates and saves a superuser
        """
        user = self.create_user(
            username=username,
            password=password,
            name=name,
        )
        # user.is_admin = True
        user.is_superuser=True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    # email = models.EmailField(
    #     verbose_name='email address',
    #     max_length=255,
    #     unique=True,
    # )
    # date_of_birth = models.DateField()
    # is_admin = models.BooleanField(default=False)
    username_validator = ASCIIUsernameValidator()
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_(
            'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    name = models.TextField()
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    profile = models.TextField(blank=True)
    picture = models.ForeignKey(
        BlobStorage, on_delete=models.CASCADE, related_name='user_picture', blank=True, null=True)
    objects = UserManager()

    USERNAME_FIELD = 'username'
    # REQUIRED_FIELDS = ['date_of_birth']

    # def __str__(self):
    #     return self.email

    # def has_perm(self, perm, obj=None):
    #     "Does the user have a specific permission?"
    #     # Simplest possible answer: Yes, always
    #     return True

    # def has_module_perms(self, app_label):
    #     "Does the user have permissions to view the app `app_label`?"
    #     # Simplest possible answer: Yes, always
    #     return True

    # @property
    # def is_staff(self):
    #     "Is the user a member of staff?"
    #     # Simplest possible answer: All admins are staff
    #     return self.is_admin
    