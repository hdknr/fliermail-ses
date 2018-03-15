from django.core.mail.backends import base
from django.utils.functional import cached_property
from email.utils import parseaddr
from .signals import BackendSignal
from .aws import SendRawEmailResponse


class SesBackend(base.BaseEmailBackend, BackendSignal):

    def __init__(self, fail_silently=False, **kwargs):
        self.source = kwargs.pop('source', None)    # SES source
        super(SesBackend, self).__init__(fail_silently=False, **kwargs)

    def send_messages(self, email_messages):
        '''Django API for Email Backend
        '''
        num = 0
        for msg in email_messages:
            if self._send(msg):
                num = num + 1
        return num

    def _resolve_sender(self, sender):
        from .models import Source
        label, address = parseaddr(sender)
        self.source = Source.objects.filter(address=address).first()

    def _send(self, message):
        try:
            if not self.source:
                self._resolve_sender(message.from_email)
            res = self.source.send_message(message)
            self.signal_success(message, res)
            return True
        except Exception as ex:
            self.signal_failure(message, ex)
            return False

    def signal_success(self, message, res):
        res = SendRawEmailResponse(res)
        self.sent_signal.send(
            sender=self.__class__,
            from_email=message.from_email,
            to=message.recipients(),
            message_id=message.message().get('Message-ID', None),
            key=res.SendRawEmailResult.MessageId,
            status_code='SendRawEmailResponse',
            message=res.format())

    def signal_failure(self, message, ex):
        message_id = message.message().get('Message-ID', None)
        self.failed_signal.send(
            sender=self.__class__,
            from_email=message.from_email,
            to=message.recipients(),
            message_id=message_id,
            key=message_id,             # no key given
            status=ex.__class__.__name__, message=str(ex))
