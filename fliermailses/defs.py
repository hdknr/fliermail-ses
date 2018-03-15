from django.db import models
from django.utils.translation import ugettext_lazy as _


class BaseModel(models.Model):
    '''Base Model
    '''
    created_at = models.DateTimeField(_(u'Created At'), auto_now_add=True, )
    updated_at = models.DateTimeField(_(u'Updated At'), auto_now=True, )

    class Meta:
        abstract = True


class Topic(BaseModel):
    BOUNCE = 0
    COMPLAINT = 1
    DELIVERY = 2

    NOTIFICATION_TYPES = ['Bounce', 'Complaint', 'Delivery']

    topic = models.IntegerField(
        _('Topic'), choices=(
            (BOUNCE, _('Bounce Topic')),
            (COMPLAINT, _('Complaint Topic')),
            (DELIVERY, _('Delivery Topic')),), default=BOUNCE)

    arn = models.CharField(
        _('Topic Arn'),
        help_text=_('Topic Arn Help'),
        max_length=100, null=True, default=None, blank=True)

    class Meta:
        abstract = True


class Service(BaseModel):
    name = models.CharField(
        _('Service Name'),
        help_text=_('Service Name Help'), max_length=100)

    region = models.CharField(
        _('SES Region'), help_text=_('SES Region Help'),
        max_length=30, null=True, default=None, blank=True)

    key = models.CharField(
        _('SES Access Key'),
        help_text=_('SES Access Key Help'),
        max_length=100, null=True, default=None, blank=True)

    secret = models.CharField(
        _('SES Access Secret'),
        help_text=_('SES Access Secret Help'),
        max_length=100, null=True, default=None, blank=True)

    settings = models.TextField(
        _('Settings'), null=True, default=None, blank=True)

    class Meta:
        abstract = True


class Source(BaseModel):
    name = models.CharField(
        _('Sender Name'), help_text=_('Sender Name Help'),
        max_length=100)
    address = models.EmailField(
        _('Sender Address'), max_length=100)

    arn = models.CharField(
        _('Source Identity Arn'), help_text=_('Source Identity Arn Help'),
        max_length=100, null=True, default=None, blank=True)

    class Meta:
        abstract = True



class Notification(BaseModel):
    message = models.TextField(
        _('SNS Message'), help_text=_('SNS Message'),)

    headers = models.TextField(
        _('SNS Headers'), help_text=_('SNS Headers Help'),
        null=True, blank=True, default='')

    class Meta:
        abstract = True


class Certificate(BaseModel):
    cert_url = models.URLField(_('Certificate URL'))
    cert = models.TextField(
        _('Certificate'), null=True, default=None, blank=True)

    class Meta:
        abstract = True
