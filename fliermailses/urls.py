from django.conf.urls import path
from . import views


urlpatterns = [
    path('notify/<str:topic>/', views.notify, name='fliermailses_notify'),
]
