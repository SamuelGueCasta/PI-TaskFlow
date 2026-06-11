from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv
import os

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)

async def enviar_email_recuperacion(email_destino: str, token: str):
    enlace = f"http://192.168.1.14:8000/auth/resetear-contrasena?token={token}"
    
    mensaje = MessageSchema(
        subject="Recuperación de contraseña - TaskFlow",
        recipients=[email_destino],
        body=f"""
        <h2>Recuperación de contraseña</h2>
        <p>Has solicitado restablecer tu contraseña en TaskFlow.</p>
        <p>Haz clic en el siguiente enlace para continuar:</p>
        <a href="{enlace}">Restablecer contraseña</a>
        <p>Este enlace expira en 1 hora.</p>
        <p>Si no has solicitado este cambio, ignora este mensaje.</p>
        """,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(mensaje)