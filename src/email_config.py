import os
import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import DBProvaiderError, ConnectionErrors, ApiError
from starlette.responses import JSONResponse

conf = ConnectionConfig(
    MAIL_USERNAME=os.environ["MAIL_USERNAME"],
    MAIL_FROM=os.environ["MAIL_FROM"],
    MAIL_PORT=os.environ["MAIL_PORT"],
    MAIL_SERVER=os.environ["MAIL_SERVER"],
    MAIL_FROM_NAME=os.environ["MAIL_FROM_NAME"],
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=False,
    MAIL_PASSWORD=os.environ["MAIL_PASSWORD"],
    USE_CREDENTIALS=False,
    VALIDATE_CERTS=False
)

async def send_reset_password_mail(email: str, 
                                   token: str, 
                                   ) -> JSONResponse:
    body = f"""
            <html>
            <body>
            <h3>Recuperação de acesso</h3>
            <p>Olá, {email}.</p>
            <p>Você esqueceu sua senha da API PGD.
            Segue o token para geração de nova senha: <br/> {token}
            </p>
            </body>
            </html>
            """
    try:
        message = MessageSchema(
            subject="Recuperação de acesso",
            recipients=[email],
            body=body,
            subtype=MessageType.html
        )
        fm = FastMail(conf)
        await fm.send_message(message)
        return JSONResponse(status_code=200, content={"message": "Email enviado!"})
    except (DBProvaiderError, ConnectionErrors, ApiError) as e:
        logging.error("Erro ao enviar o email %e", e)
    finally:
        raise e
