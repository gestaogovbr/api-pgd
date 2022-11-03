from fastapi_mail import ConnectionConfig

conf = ConnectionConfig(
    MAIL_USERNAME="api-pgd@economia.gov.br",
    MAIL_FROM="api-pgd@economia.gov.br",
    MAIL_PORT=25,
    MAIL_SERVER="mail-apl.serpro.gov.br",
    MAIL_FROM_NAME="API PGD",
    MAIL_TLS=False,
    MAIL_SSL=False,
    MAIL_PASSWORD="",
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False
)

