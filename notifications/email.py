"""Envio de alertas por SMTP configurado no ambiente."""

import os
import smtplib
from email.message import EmailMessage


def enviar_email(destinatario, assunto, corpo):
    host = os.getenv("SMTP_HOST")
    remetente = os.getenv("EMAIL_REMETENTE")
    usuario = os.getenv("SMTP_USER")
    senha = os.getenv("SMTP_PASSWORD")
    if not all((host, remetente, usuario, senha)):
        raise RuntimeError(
            "Configure SMTP_HOST, EMAIL_REMETENTE, SMTP_USER e SMTP_PASSWORD."
        )
    if not destinatario.strip():
        raise ValueError("O destinatário do email é obrigatório.")

    mensagem = EmailMessage()
    mensagem["From"] = remetente
    mensagem["To"] = destinatario
    mensagem["Subject"] = assunto
    mensagem.set_content(corpo)

    porta = int(os.getenv("SMTP_PORT", "587"))
    with smtplib.SMTP(host, porta, timeout=20) as servidor:
        servidor.starttls()
        servidor.login(usuario, senha)
        servidor.send_message(mensagem)
