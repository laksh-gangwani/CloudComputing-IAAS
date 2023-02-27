import logging
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from Utils import AWSUtils
from Classifier.ImageClassifier import ImageClassifier
from Properties import AppTierProperties

log = logging.getLogger(__name__)

if __name__ == "__main__":
    log.info("Starting IAAS App Tier Application")
    aws_utils = AWSUtils.AWSUtils()
    image_classifier = ImageClassifier()
    image_classifier.start_classifier()
    log.info("AppTier Instance Shutting Down")
