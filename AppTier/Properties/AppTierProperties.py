class AppTierProperties:
    REQUEST_SQS = "RequestQueue"
    RESPONSE_SQS = "ResponseQueue"

    REQUEST_S3 = "infra-bucket1-m3pxpzoyq0kc"
    RESPONSE_S3 = "infra-bucket2-11ixq7ltu7hkx"

    AWS_ACCESS_KEY = ""
    AWS_SECRET_KEY = ""

    @property
    def aws_credentials(self):
        return {
            "aws_access_key_id": self.AWS_ACCESS_KEY,
            "aws_secret_access_key": self.AWS_SECRET_KEY
        }
