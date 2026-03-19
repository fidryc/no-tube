from app.core.config import settings

def generate_oauth_redirect_url():
    query_params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": "http://localhost:5173/callback",
        "scope": " ".join(["openid", "email", "profile"]),
        "response_type": "code",
        "access_type": "offline",
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{'&'.join([f'{key}={value}' for key, value in query_params.items()])}"