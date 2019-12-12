from django.db import models


class DummyFile(models.Model):
    uploadedfile = models.FileField(blank=True, default='')
