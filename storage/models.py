from django.db import models

class BlobStorage(models.Model):
    data = models.BinaryField()

    def __str__(self):
        return self.id
