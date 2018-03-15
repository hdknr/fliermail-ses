from django.db import models
from . import encoders


class NotificationQuerySet(models.QuerySet):

    def create(self, meta, message, **kwargs):
        kwargs['headers'] = encoders.to_json(meta)
        return super(
            NotificationQuerySet, self).create(message=message, **kwargs)
