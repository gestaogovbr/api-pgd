import pytest
from fastapi_mail import FastMail, MessageSchema
from email_conf import conf

@pytest.mark.asyncio
async def test_send_email():
    "Testa o envio de email"

    message = MessageSchema(
        subject='test subject',
        recipients=['testx@api.com'],
        body='test',
        subtype='plain',
    )

    fm = FastMail(conf)

    await fm.send_message(message)

    assert message.body == 'test'
    assert message.subtype == 'plain'