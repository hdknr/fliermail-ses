'''
AWS SES :http://boto.readthedocs.org/en/latest/ref/ses.html
'''
from django.core.mail.message import EmailMultiAlternatives
from django.contrib.sites.models import Site
from django.utils.functional import cached_property
try:
    from django.urls import reverse
except:
    from django.core.urlresolvers import reverse

import json
from datetime import datetime
from email.header import Header
import requests
from . import aws, defs, signals, backends

import traceback
from logging import getLogger
logger = getLogger('fliermailses')


class Service(object):

    def cert(self, url):
        cert = self.certificate_set.filter(cert_url=url).first()
        if not cert:
            cert = self.certificate_set.create(
                cert_url=url,
                cert=requests.get(url).text)
        return cert

    @cached_property
    def all_regions(self):
        return aws.get_ses_regions()

    @cached_property
    def region_info(self):
        res = next(
            filter(lambda i: i == self.region, self.all_regions))
        return res

    @cached_property
    def connection(self):
        return aws.connect_ses(
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
            region_name=self.region_info)

    @cached_property
    def sns_connection(self):
        regions = aws.get_sns_regions(self.region)
        return aws.connect_sns(
            aws_access_key_id=self.key,
            aws_secret_access_key=self.secret,
            region=regions[0])

    def verify_email_address(self, email):
        '''
        Verifies an email address.
        This action causes a confirmation email message
        to be sent to the specified address.
        '''
        addresses = self.list_verified_email_addresses()
        if email not in addresses:
            res = self.connection.verify_email_address(email)
            return res

    def list_verified_email_addresses(self):
        '''
        A ListVerifiedEmailAddressesResponse structure.
        Note that keys must be unicode strings.
        '''
        data = self.connection.list_verified_email_addresses()
        res = aws.ListVerifiedEmailAddressesResponse(data)
        return res.addresses


class Source(object):
    @cached_property
    def connection(self):
        return self.service.connection

    @cached_property
    def backend(self):
        '''
        >>>from django.core import mail
        >>>mail.get_connection(
        ...    'fliermailses.backends.SesBackend', connection=self)
        '''
        return backends.SesBackend(connection=self)

    @cached_property
    def sender(self):
        name = Header(self.name).encode('ISO-2022-JP')
        return f"{name} <{self.address}>"

    def create_message(self, **kwargs):
        '''
        https://docs.djangoproject.com/en/2.0/topics/email/#sending-alternative-content-types
        '''
        kwargs.pop('from_email', None)
        kwargs.pop('connection', None)
        headers = kwargs.pop('headers', {})
        headers['From'] = self.sender
        return EmailMultiAlternatives(
            from_email=self.address,            # Only Verified Address
            connection=self.backend,            # IMPORTANT: SesBackend
            headers=headers, **kwargs
        )

    def send_email(self, recipients, subject, text, html=None, charset="utf-8"):
        '''AWS SES API
        redipients : list of address
        '''
        destination = {'ToAddresses': recipients, }
        body = {'Text': {'Charset': charset, 'Data': text}, }
        if html:
            body['Html'] = {'Charset': charset, 'Data': html}
        subject = {'Charset': charset, 'Data': subject,}
        message = {'Body': body, 'Subject': subject}

        return self.connection.send_email(
            Destination=destination, Message=message, Source=self.sender)

    def send_raw_email(self, raw_message, destinations):
        '''AWS SES API'''
        return self.connection.send_raw_email(
            Source=self.sender,
            RawMessage={'Data': raw_message.encode()},
            Destinations=destinations,
        )

    def cert(self, url):
        return self.service.cert(url)

    def verify_address(self, address=None):
        '''
        http://boto.readthedocs.org/en/latest/ses_tut.html
        #verifying-a-sender-email-address
        '''
        address = address or self.address
        if address:
            self.connection.verify_email_address(address)

    def set_notification(self):
        '''
        http://boto.readthedocs.org/en/latest/ref/ses.html?
        highlight=ses
        #boto.ses.connection.SESConnection.set_identity_notification_topic
        '''
        for topic in self.topic_set.all():
            self.connection.set_identity_notification_topic(
                self.address,
                topic.NOTIFICATION_TYPES[topic.topic],
                topic.arn)
            # TOOD: ERROR HANDLING


    def create_topic(self, notification, site=None, scheme='http'):
        site = site or Site.objects.first()
        if notification in defs.Topic.NOTIFICATION_TYPES:
            topic = defs.Topic.NOTIFICATION_TYPES.index(notification)
            topic_name = u"{}-{}-topic".format(self.service.name, notification)
            endpoint = "{}://{}{}".format(
                scheme, site.domain,
                reverse('fliermailses_notify', kwargs={'topic': notification}))
            arn = aws.create_ses_notification(
                self.service.sns_connection,
                self.service.connection,
                topic_name, endpoint, self.address, notification)

            if not self.topic_set.filter(topic=topic).update(arn=arn):
                self.topic_set.create(topic=topic, arn=arn)


class Notification(signals.NotificationSignal):

    @cached_property
    def message_object(self):
        return aws.SnsMessage(self.message)

    @cached_property
    def headers_object(self):
        return json.loads(self.headers)

    @property
    def _topic(self):
        if not self.topic_id:
            field = self._meta.get_field('topic')
            self.topic = field.related_model.objects.filter(
                arn=self.message_object.TopicArn).first()
            if self.topic:
                self.save()
        return self.topic_id and self.topic

    @property
    def cert(self):
        topic = self._topic
        return topic.source.cert(self.message_object.SigningCertURL)

    def is_valid(self):
        cert = self.cert
        return self.message_object.verify(cert.cert)

    def signal(self):
        signal = None
        if self.message_object.Type in [
            'SubscriptionConfirmation', 'UnsubscribeConfirmation'
        ]:
            signal = self.confirm_signal
        elif self.message_object.Type in ['Notification']:
            signal = dict(
                Complaint=self.complaint_signal,
                Bounce=self.bounce_signal,
                Delivery=self.delivery_signal,
            ).get(self.message_object.Message.notificationType, None)

        try:
            signal and signal.send(sender=type(self), instance=self)
        except:
            logger.error(traceback.format_exc())

    def confirm(self):
        self.message_object.confirm_subscribe_url()

    def get_address_list(self):
        return self.message_object.get_address_list()

    def get_message(self):
        return self.message


class Certificate(object):
    pass
