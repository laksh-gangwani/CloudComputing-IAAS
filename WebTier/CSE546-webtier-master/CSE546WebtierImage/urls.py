from django.urls import path

from . import imagepushcontroller

urlpatterns = [
    path('push', imagepushcontroller.pushcontroller),
    path('ping', imagepushcontroller.pingcontroller)
]

from . import imagequeue

imagequeue.init()