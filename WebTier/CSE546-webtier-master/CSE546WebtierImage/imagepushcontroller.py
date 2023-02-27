from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from . import imagequeue

@csrf_exempt
def pingcontroller(request) :
    return HttpResponse("pong")

@csrf_exempt
def pushcontroller(request) :
    if 'myfile' not in request.FILES :
        return HttpResponse('error: myfile must be present', status = 400)
    image_filename = request.FILES['myfile'].name
    image_content = request.FILES['myfile'].open('rb').read()
    imagequeue.markRequiredToReceiveMessage(image_filename)
    imagequeue.sendImage(image_filename, image_content)
    result = imagequeue.waitForResultFromReceivedMessage(image_filename, timeout = 15 * 60.0) # timesouts in 5 minutes
    if(result == None) :
        print("sending 500 due to a timeout")
        return HttpResponse('error: timeout on receiving response', status = 500)
    return HttpResponse(result)