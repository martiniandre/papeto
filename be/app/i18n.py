"""User-facing text the backend sends itself (e-mails). pt-BR first; the app translates API error
codes on its own, so only messages that leave the server without the app live here.

Copy is a draft: product must review it before launch.
"""

from __future__ import annotations

DEFAULT_LANGUAGE = "pt-BR"

MESSAGES: dict[str, dict[str, str]] = {
    "pt-BR": {
        "password_reset.subject": "Redefinir sua senha do Papeto",
        "password_reset.body": (
            "Olá!\n\n"
            "Recebemos um pedido para redefinir a senha da sua conta no Papeto.\n"
            "Para criar uma nova senha, abra este link em até {minutes} minutos:\n\n"
            "{link}\n\n"
            "Se não foi você, é só ignorar este e-mail. Sua senha continua a mesma."
        ),
    },
}


def translate(key: str, language: str = DEFAULT_LANGUAGE, **values: str | int) -> str:
    """Text for `key` in `language`, falling back to pt-BR. Raises KeyError for unknown keys."""
    table = MESSAGES.get(language, MESSAGES[DEFAULT_LANGUAGE])
    template = table.get(key, MESSAGES[DEFAULT_LANGUAGE][key])
    return template.format(**values)
