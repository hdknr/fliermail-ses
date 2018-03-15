import json
import requests
import boto3
from base64 import standard_b64decode
from .crypto import verify_signature
from logging import getLogger
logger = getLogger()


# http://docs.aws.amazon.com/sns/latest/dg/
# SendMessageToHttp.verify.signature.html

NOTIFICATION_SIGNING_INPUT_KEY = [
    "Message",
    "MessageId",
    "Subject",
    "SubscribeURL",
    "Timestamp",
    "Token",
    "TopicArn",
    "Type",
]

def connect_ses(aws_access_key_id, aws_secret_access_key, region_name):
    return boto3.client('ses',
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)


def connect_sns(access_key_id, secret_access_key, region_name):
    return boto3.client('sns',
        region_name=region_name,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key)


def get_ses_regions(name=None):
    res = boto3.session.Session().get_available_regions('ses')
    return name and [ri for ri in res if ri.name == name] or res


def get_sns_regions(name=None):
    res = boto3.session.Session().get_available_regions('sns')
    return name and [ri for ri in res if ri.name == name] or res


def NOTIFICATION_SIGNING_INPUT(jobj):
    return "".join([
        "{}\n{}\n".format(k, jobj.get(k))
        for k in NOTIFICATION_SIGNING_INPUT_KEY
        if k in jobj
    ])


def create_ses_notification(
        sns_conn, ses_conn, topic_name, endpoint, identity, notification):
    topic_obj = sns_conn.create_topic(topic_name)
    logger.debug(topic_obj)

    arn = topic_obj.get(
        'CreateTopicResponse', {}).get(
            'CreateTopicResult', {}).get('TopicArn', None)
    if arn:
        result = sns_conn.subscribe(arn, 'http', endpoint)
        result = ses_conn.set_identity_notification_topic(
            identity, notification, arn)
        logger.debug(result)
        return arn


class BaseMessage(object):

    def __init__(self, data):
        if isinstance(data, str):
            self.data = json.loads(data)
        elif isinstance(data, dict):
            self.data = data
        else:
            self.data = {}

    def __getattr__(self, name):
        return self.data.get(name, None)

    def format(self, indent=2, *args, **kwargs):
        return json.dumps(self.data, indent=2, *args, **kwargs)


class SnsMessage(BaseMessage):
    '''
    - SignatureVersion, Timestamp,Signature, Type, SigningCertURL,
      MessageId, Message(SesMessage), UnsubscribeURL, TopicArn
    '''

    @property
    def Message(self):
        def _cache(self):
            if self.Type == u'Notification':
                self._Message = SesMessage(self.data['Message'])
            else:
                self._Message = SesMessage('{}')
            return self._Message

        return getattr(self, '_Message', _cache(self))

    def confirm_subscribe_url(self):
        return requests.get(self.SubscribeURL)

    @property
    def singin_input(self):
        return NOTIFICATION_SIGNING_INPUT(self.data)

    @property
    def signature(self):
        return standard_b64decode(self.Signature)

    def verify(self, cert):
        return verify_signature(
            cert, self.singin_input, self.signature)

    def get_address_list(self):
        return self.Message.get_address_list()


class SesMessage(BaseMessage):
    '''
    - notificationType,
    - mail(MailMessage)
    - bounce(BounceMessage)
    '''

    @property
    def mail(self):
        '''
        - timestamp, destination(list(address)), source, messageId,
        sendingAccountId, sourceArn
        '''
        def _cache():
            self._mail = BaseMessage(self.data.get('mail', {}))
            return self._mail

        return getattr(self, '_mail', _cache())

    @property
    def bounce(self):
        def _cache():
            self._bounce = BounceMessage(self.data.get('bounce', {}))
            return self._bounce

        return getattr(self, '_bounce', _cache())

    @property
    def delivery(self):
        '''
        - processingTimeMillis, timestamp,
          reportingMTA, recipients(list(address)),
          smtpResponse,
        '''
        def _cache():
            self._delivery = BaseMessage(self.data.get('delivery', {}))
            return self._delivery

        return getattr(self, '_delivery', _cache())

    @property
    def complaint(self):
        def _cache():
            self._complaint = ComplaintMessage(self.data.get('complaint', {}))
            return self._complaint

        return getattr(self, '_complaint', _cache())

    def get_address_list(self):
        if self.notificationType == 'Bounce':
            return self.bounce.get_address_list()

        if self.notificationType == 'Complaint':
            return self.complaint.get_address_list()

        if self.notificationType == 'Delivery':
            return self.delivery.recipients

        return []


class BounceMessage(BaseMessage):
    '''
    - feedbackId, timestamp, reportingMTA, bounceSubType, bounceType
    - bouncedRecipients: list(BounceRecipient)
    '''
    @property
    def bouncedRecipients(self):
        ''' list
        - status, diagnosticCode, emailAddress, action
        '''
        def _cache(self):
            self._bouncedRecipients = [
                BaseMessage(data) for data
                in self.data.get('bouncedRecipients', [])]
            return self._bouncedRecipients

        return getattr(self, '_bouncedRecipients', _cache(self))

    def get_address_list(self):
        return [r.emailAddress for r in self.bouncedRecipients]


class ComplaintMessage(BaseMessage):
    '''
    - complainedRecipients, userAgent, feedbackId, timestamp,
      complaintFeedbackType
    '''
    @property
    def complainedRecipients(self):
        ''' list
        - emailAddress
        '''
        def _cache(self):
            self._complainedRecipients = [
                BaseMessage(data) for data
                in self.data.get('complainedRecipients', [])]
            return self._bouncedRecipients

        return getattr(self, '_complainedRecipients', _cache(self))

    def get_address_list(self):
        return [r.emailAddress for r in self.complainedRecipients]


class SendEmailResponse(BaseMessage):

    @property
    def ResponseMetadata(self):
        def _cache(self):
            self._ResponseMetadata = BaseMessage(
                self.data.get('ResponseMetadata'))
            return self._ResponseMetadata

        return getattr(self, '_ResponseMetadata', _cache(self))

    @property
    def SendEmailResult(self):
        def _cache(self):
            self._SendEmailResult = BaseMessage(
                self.data.get('SendEmailResult'))
            return self._SendEmailResult

        return getattr(self, '_SendEmailResult', _cache(self))


class SendRawEmailResponse(SendEmailResponse):

    @property
    def SendRawEmailResult(self):
        def _cache(self):
            self._SendRawEmailResult = BaseMessage(
                self.data.get('SendRawEmailResult'))
            return self._SendRawEmailResult

        return getattr(self, '_SendRawEmailResult', _cache(self))


class ListVerifiedEmailAddressesResponse(BaseMessage):

    def __init__(self, data):
        super(ListVerifiedEmailAddressesResponse, self).__init__(data)
        self.data = self.ListVerifiedEmailAddressesResponse

    @property
    def result(self):
        return self.ListVerifiedEmailAddressesResult

    @property
    def addresses(self):
        return self.result['VerifiedEmailAddresses']
