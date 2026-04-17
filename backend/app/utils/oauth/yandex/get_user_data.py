import aiohttp

from app.utils.oauth.response import OauthAccount


async def get_yandex_user_data(oauth_token: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://login.yandex.ru/info",
            headers={"Authorization": f"OAuth {oauth_token}"}
        ) as response:
            user_data: dict = await response.json()
            if user_data.get("status", "") == "error":
                raise ValueError("Invalid token")
            return OauthAccount(
                provider_id=user_data["psuid"],
                username=user_data.get("display_name"),
                email=user_data.get("default_email"),
                is_confirmed=user_data.get("is_verified", True), # TODO: посмотреть может можно получить поле в ответе
            )