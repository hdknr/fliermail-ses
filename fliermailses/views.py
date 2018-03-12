from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, HttpResponse
from . import models


@csrf_exempt
def notify(request, topic):
    notification = models.Notification.objects.create(
        request.META, request.body)

    if not notification.is_valid():
        return HttpResponseBadRequest('bad request')

    notification.signal()

    return HttpResponse('OK')
