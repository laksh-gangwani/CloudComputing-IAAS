import boto3
import base64
import threading
import time

REQUEST_QUEUE_NAME = "RequestQueue"
RESPONSE_QUEUE_NAME = "ResponseQueue"
REGION_NAME = "us-east-1"
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

sqs = None
ResponseQueue = None
ReceiverThread = None
ReceivedMessages = None
ReceivedMessagesLock = None
ReceivedMessagesConditionVariable = None

REQUIRED_SYM = "xN<--required--deriuqer-->Nx"

def markRequiredToReceiveMessage(image_filename) :
    global ReceivedMessages
    global ReceivedMessagesLock
    global ReceivedMessagesConditionVariable
    ReceivedMessagesLock.acquire()
    if(image_filename not in ReceivedMessages) :
        ReceivedMessages[image_filename] = []
    ReceivedMessages[image_filename].append(REQUIRED_SYM)
    ReceivedMessagesLock.release()

def unmarkRequiredToReceiveMessage_UNSAFE(image_filename) :
    global ReceivedMessages
    global ReceivedMessagesLock
    global ReceivedMessagesConditionVariable
    if(image_filename in ReceivedMessages) :
        for i in range(0, len(ReceivedMessages[image_filename])) :
            if(ReceivedMessages[image_filename][i] == REQUIRED_SYM) :
                del ReceivedMessages[image_filename][i]
                if(len(ReceivedMessages[image_filename]) == 0) :
                    del ReceivedMessages[image_filename]
                ReceivedMessagesConditionVariable.notifyAll()
                break

def setResultToReceivedMessage(image_filename, image_result) :
    global ReceivedMessages
    global ReceivedMessagesLock
    global ReceivedMessagesConditionVariable
    ReceivedMessagesLock.acquire()
    if(image_filename in ReceivedMessages) :
        for i in range(0, len(ReceivedMessages[image_filename])) :
            if(ReceivedMessages[image_filename][i] == REQUIRED_SYM) :
                ReceivedMessages[image_filename][i] = image_result
                ReceivedMessagesConditionVariable.notifyAll()
                break
    ReceivedMessagesLock.release()

def waitForResultFromReceivedMessage(image_filename, timeout = None) :
    global ReceivedMessages
    global ReceivedMessagesLock
    global ReceivedMessagesConditionVariable
    ReceivedMessagesLock.acquire()
    image_result = None
    while True :
        is_marked_required = False
        if(image_filename in ReceivedMessages) :
            for i in range(0, len(ReceivedMessages[image_filename])) :
                if(ReceivedMessages[image_filename][i] != REQUIRED_SYM) :
                    image_result = ReceivedMessages[image_filename][i]
                    del ReceivedMessages[image_filename][i]
                    if(len(ReceivedMessages[image_filename]) == 0) :
                        del ReceivedMessages[image_filename]
                    break
                else :
                    is_marked_required = True
        else :
            break
        if(image_result == None and is_marked_required == True and (timeout == None or timeout > 0.0)) :
            elapsed_time = time.time()
            was_notified = ReceivedMessagesConditionVariable.wait(timeout)
            elapsed_time = time.time() - elapsed_time
            if(timeout != None) :
                timeout -= elapsed_time
        else :
            break
    if(image_result == None) :
        unmarkRequiredToReceiveMessage_UNSAFE(image_filename)
    ReceivedMessagesLock.release()
    return image_result

def init() :
    global sqs
    global ResponseQueue
    global ReceiverThread
    global ReceivedMessages
    global ReceivedMessagesLock
    global ReceivedMessagesConditionVariable
    sqs = boto3.resource('sqs', region_name = REGION_NAME, aws_access_key_id = AWS_ACCESS_KEY_ID, aws_secret_access_key = AWS_SECRET_ACCESS_KEY)
    RequestQueue = sqs.get_queue_by_name(QueueName = REQUEST_QUEUE_NAME)
    ResponseQueue = sqs.get_queue_by_name(QueueName = RESPONSE_QUEUE_NAME)
    print("RequestQueue and ResponseQueue initialized")
    ReceivedMessages = {}
    ReceivedMessagesLock = threading.Lock()
    ReceivedMessagesConditionVariable = threading.Condition(ReceivedMessagesLock)
    ReceiverThread = threading.Thread(target = receiverThreadFunction)
    ReceiverThread.start()
    print("Received Thread started")

def sendImage(name, image) :
    RequestQueue = sqs.get_queue_by_name(QueueName = REQUEST_QUEUE_NAME)
    return RequestQueue.send_message(MessageBody = name + ':' + base64.b64encode(image).decode("ascii"))

def parse_message(data) :
    splits = data.split(':', 1)
    return splits[0], splits[1]

def receiverThreadFunction() :
    global ResponseQueue
    while(True) :
        for message in ResponseQueue.receive_messages(WaitTimeSeconds=20):
            message_content = message.body
            if(message_content.find(":") == -1) :
                message.delete()
                continue
            image_filename, image_result = parse_message(message_content)
            setResultToReceivedMessage(image_filename, image_result)
            message.delete()