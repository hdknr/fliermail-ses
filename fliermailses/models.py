from django.db import models
from django.utils.translation import ugettext_lazy as _
from . import defs, methods, querysets


class Service(defs.Service, methods.Service):

    class Meta:
        verbose_name = _('SES Service')
        verbose_name_plural = _('SES Service')

    def __str__(self):
        return self.name


class Source(defs.Source, methods.Source):
    service = models.ForeignKey(
        Service, verbose_name=_('Service'), help_text=_('Service Help'),
        on_delete=models.SET_NULL,
        null=True, blank=True, default=None, )

    class Meta:
        verbose_name = _('SES Source')
        verbose_name_plural = _('SES Source')

    def __str__(self):
        return "ses:{0}".format(self.address)


class Topic(defs.Topic):
    source = models.ForeignKey(
        Source, null=True, blank=True, default=None,
        on_delete=models.SET_NULL, )

    class Meta:
        verbose_name = _('SNS Topic')
        verbose_name_plural = _('SNS Topic')
        unique_together = (('source', 'topic', ), )

    def __str__(self):
        return u"{0} {1}".format(
            self.source.__str__(),
            self.get_topic_display())


class Notification(defs.Notification, methods.Notification):
    topic = models.ForeignKey(
        Topic, null=True, blank=True, default=None,
        on_delete=models.SET_NULL, )

    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notification')

    objects = querysets.NotificationQuerySet.as_manager()


class Certificate(defs.Certificate, methods.Certificate):
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, )

    class Meta:
        verbose_name = _('SES Certificate')
        verbose_name_plural = _('SES Certificate')
