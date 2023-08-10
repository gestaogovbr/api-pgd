import os
from fastapi_mail import ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME=os.environ["MAIL_USERNAME"],
    MAIL_FROM=os.environ["MAIL_FROM"],
    MAIL_PORT=os.environ["MAIL_PORT"],
    MAIL_SERVER=os.environ["MAIL_SERVER"],
    MAIL_FROM_NAME=os.environ["MAIL_FROM_NAME"],
    MAIL_TLS=False,
    MAIL_SSL=False,
    MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False
)

