from aiosmtplib import send, SMTPException
from app.core.config import settings
from app.core.logger import logger
from fastapi import HTTPException, status


async def send_email(msg_email: dict):
    recipient = msg_email.get('To', 'Unknown')
    try:
        await send(
            msg_email,
            port=settings.SMTP_PORT,
            hostname=settings.SMTP_HOST,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASS,
            use_tls=True
        )
        logger.info('Email sent successfully (async)', extra={'recipient': recipient})
    except SMTPException as e: pass # TODO: преобразование ошибки