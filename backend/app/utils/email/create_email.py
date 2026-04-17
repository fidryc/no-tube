from email.message import EmailMessage
from app.core.config import settings

def confirm_email(email_to: str, code: str):
    email_message = EmailMessage()
    email_message['Subject'] = 'Уведомление о регистрации на notube'
    email_message['From'] = settings.SMTP_USER
    email_message['To'] = email_to
    
    
    # TODO: Добавить константы для ссылки
    email_message.set_content(
        f"""
        <h1>Вы пытаетесь зарегистрироваться на notube</h1>
        Подвердите почту перейдя по ссылке: http://127.0.0.1:8000/api/v1/user/confirm?token={code}
        """,
        subtype='html'
    )
    return email_message