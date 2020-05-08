from django.db import models

class BlobStorage(models.Model):
    data = models.BinaryField()
