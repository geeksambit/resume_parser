from django.db import models
import uuid

# Create your models here.
class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    file = models.FileField(upload_to='uploads/')

    def __str__(self):
        return '{}'.format(self.name)