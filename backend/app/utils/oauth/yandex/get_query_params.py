from app.core.config import settings

def get_query_params() -> dict:
    return {
        "client_id": settings.YANDEX_CLIENT_ID,
        "response_type": "token",
        "redirect_uri": "http://localhost:5173/callback_yandex" # TODO: move to config
    }