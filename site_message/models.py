from django.db import models

from account.models import User


class Message(models.Model):
    title = models.CharField(max_length=255)
    send_date = models.DateTimeField()
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='message_sender')
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='message_recipient')
    content = models.TextField()
    is_unread = models.BooleanField(default=True)
    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_recipient = models.BooleanField(default=False)
