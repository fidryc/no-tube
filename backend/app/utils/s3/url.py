from app.core.config import settings

def build_url(key: str) -> str:
    return f"{settings.PUBLIC_VIDEO_BASE_URL}/{settings.PUBLIC_BUCKET}/{key}"