import logging
import os
import subprocess
import base64
from PIL import Image
from io import BytesIO
from AppTier.Utils import AWSUtils, AppTierProperties


log = logging.getLogger(__name__)

class ImageClassifier:
    def __init__(self, request_queue_name=None, response_queue_name=None, request_bucket_name=None, response_bucket_name=None):
        self.aws_utils = AWSUtils(request_queue_name, response_queue_name, request_bucket_name, response_bucket_name)

    def start_classifier(self):
        loop = True
        while loop:
            try:
                message = self.aws_utils.receive_message_from_request_queue()
                image_data = base64.b64decode(message['Body'])
                img = Image.open(BytesIO(image_data))

                recognition_result = self.get_result(img)

                response_content = recognition_result.encode('utf-8')
                self.aws_utils.upload_to_response_s3(message['MessageId'], response_content)

                self.aws_utils.send_message_to_request_queue(recognition_result)

                self.aws_utils.delete_message_from_request_queue(message)
            except Exception as e:
                log.exception(f"An error occurred while processing the message: {e}")
                loop = False

    def get_result(self, img):
        try:
            with BytesIO() as image_binary:
                img.save(image_binary, format='JPEG')
                image_bytes = image_binary.getvalue()

            command = ["python", "image_classification.py", "-"]
            log.info(f"Command being executed on AppTier: {command}")

            with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=100) as process:
                stdout, stderr = process.communicate(input=image_bytes)

            if process.returncode == 0:
                return stdout.decode().strip()
            else:
                return f"Timeout for image recognition passed no result. Error: {stderr.decode().strip()}"
        except subprocess.TimeoutExpired:
            return "Timeout for image recognition passed no result"
