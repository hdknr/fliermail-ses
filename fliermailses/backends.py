from django.core.mail.backends import base
from .aws import SendRawEmailResponse
from .signals import BackendSignal

from django.core.mail.backends import base
from flier.backends import BackendSignal
from flier.ses.aws import SendRawEmailResponse


class SesBackend(base.BaseEmailBackend, BackendSignal):

    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently

        # boto connection
        self.connection = kwargs.get('connection', None)

    def send_messages(self, email_messages):
        '''Django API for Email Backend
        '''
        num = 0
        for msg in email_messages:
            self._send(msg)
            num = num + 1
        return num

    def _send(self, message):
        '''
        - http://bit.ly/flier_ses_sendrawemail
        '''
        from .models import Source
        sender = message.from_email
        if not self.connection:
            self.connection = Source.objects.filter(
                address=sender).first().connection

        recipients = message.recipients()
        for to in recipients:
            self._send_single(message,  sender, to)

        return True

    def _send_single(self, message, sender, destinations):
        try:
            message_id = message.extra_headers.get('Message-ID')
            res = self.connection.send_raw_email(
                raw_message=message.message().as_string(),
                source=sender, destinations=destinations,)

            res = SendRawEmailResponse(res['SendRawEmailResponse'])

            self.sent_signal.send(
                sender=self.__class__,
                from_email=sender, to=destinations, message_id=message_id,
                key=res.SendRawEmailResult.MessageId,
                status_code='SendRawEmailResponse', message=res.format())
        except Exception as ex:
            self.failed_signal.send(
                sender=self.__class__,
                from_email=sender, to=destinations, message_id=message_id,
                key=message_id,             # no key given
                status=ex.__class__.__name__, message=ex.message)
