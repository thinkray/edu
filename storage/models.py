from django.db import models


class BlobStorage(models.Model):
    data = models.BinaryField()
    content_type = models.CharField(max_length=255)
