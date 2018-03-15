from django.core.mail.backends import base
from django.utils.functional import cached_property

from .signals import BackendSignal
from .aws import SendRawEmailResponse


class SesBackend(base.BaseEmailBackend, BackendSignal):

    def __init__(self, fail_silently=False, **kwargs):
        self.fail_silently = fail_silently

        # SES source
        self.source = kwargs.get('source', None)

    def send_messages(self, email_messages):
        '''Django API for Email Backend
        '''
        num = 0
        for msg in email_messages:
            if self._send(msg):
                num = num + 1
        return num

    def _send(self, message):
        from .models import Source
        sender = message.from_email
        if not self.source:
            self.source = Source.objects.filter(address=sender).first()
        recipients = message.recipients()
        return self._send_ses(message,  sender, recipients)

    def _send_ses(self, message, sender, destinations):
        try:
            res = self.source.send_raw_email(
                raw_message=message.message().as_string(),
                destinations=destinations)

            res = SendRawEmailResponse(res)
            message_id = message.extra_headers.get('Message-ID', None)
            self.sent_signal.send(
                sender=self.__class__,
                from_email=sender, to=destinations, message_id=message_id,
                key=res.SendRawEmailResult.MessageId,
                status_code='SendRawEmailResponse', message=res.format())
            return True

        except Exception as ex:
            self.failed_signal.send(
                sender=self.__class__,
                from_email=sender, to=destinations, message_id=message_id,
                key=message_id,             # no key given
                status=ex.__class__.__name__, message=str(ex))
            return False
