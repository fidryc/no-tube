from app.tasks.broker import broker
from app.utils.email.create_email import confirm_email
from app.utils.email.send import send_email

@broker.task
async def send_code_task(email_to: str, code: str):
    email = confirm_email(email_to, code)
    await send_email(email)