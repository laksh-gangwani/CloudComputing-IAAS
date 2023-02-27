import boto3
from botocore.exceptions import ClientError
from typing import Optional
from Properties.AppTierProperties import AppTierProperties
import logging

logger = logging.getLogger(__name__)

class AWSUtils:
    def __init__(self, request_queue_name: Optional[str] = None, response_queue_name: Optional[str] = None,
                 request_bucket_name: Optional[str] = None, response_bucket_name: Optional[str] = None):
        self.request_queue_name = request_queue_name or AppTierProperties.REQUEST_SQS
        self.response_queue_name = response_queue_name or AppTierProperties.RESPONSE_SQS
        self.request_bucket_name = request_bucket_name or AppTierProperties.REQUEST_S3
        self.response_bucket_name = response_bucket_name or AppTierProperties.RESPONSE_S3

        self.sqs = boto3.client('sqs', region_name='us-east-1', aws_access_key_id=AppTierProperties.AWS_ACCESS_KEY,
                                aws_secret_access_key=AppTierProperties.AWS_SECRET_KEY)
        self.s3 = boto3.client('s3', region_name='us-east-1', aws_access_key_id=AppTierProperties.AWS_ACCESS_KEY,
                               aws_secret_access_key=AppTierProperties.AWS_SECRET_KEY)

    def send_message_to_response_queue(self, message: str) -> None:
        try:
            queue_url = self.sqs.get_queue_url(QueueName=self.response_queue_name)['QueueUrl']
            self.sqs.send_message(QueueUrl=queue_url, MessageBody=message)
        except ClientError as e:
            logger.exception(f"Error sending message to Request Queue: {e}")

    def receive_message_from_request_queue(self):
        try:
            queue_url = self.sqs.get_queue_url(QueueName=self.request_queue_name)['QueueUrl']
            response = self.sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20)
            messages = response.get("Messages", [])
            if not messages:
                return None
            message = messages[0]
            return message
        except ClientError as e:
            logger.exception(f"Error receiving message from Request Queue: {e}")

    def delete_message_from_sqs(self, message: dict) -> None:
        try:
            queue_url = self.sqs.get_queue_url(QueueName=self.request_queue_name)['QueueUrl']
            receipt_handle = message['ReceiptHandle']
            self.sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        except ValueError as e:
            logger.exception(f"Error deleting message from SQS: {e}")

    def download_from_request_s3(self, object_key: str) -> bytes:
        try:
            response = self.s3.get_object(Bucket=self.request_bucket_name, Key=object_key)
            content = response['Body'].read()
            return content
        except ClientError as e:
            logger.exception(f"Error downloading object from Request S3: {e}")

    def upload_to_response_s3(self, object_key: str, content: bytes) -> None:
        try:
            self.s3.put_object(Bucket=self.response_bucket_name, Key=object_key, Body=content)
        except ClientError as e:
            logger.exception(f"Error uploading object to Response S3: {e}")

