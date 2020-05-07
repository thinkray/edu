from django.db import models
from account.models import User


class Log(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='log_user')
    date = models.DateTimeField()
    operation = models.TextField()

    def __str__(self):
        return self.user + ':' + self.date + ':' + self.operation
