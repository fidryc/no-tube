from dataclasses import dataclass
import email

import aiohttp
from app.core.config import settings
from jose import jwt, JWTError

from app.core.logger import logger


@dataclass
class GoogleUserInfo:
    sub: str
    email: str
    email_verified: bool
    name: str


async def get_user_info(code: str) -> GoogleUserInfo:
    params = params_for_get_user_info(code)
    async with aiohttp.ClientSession() as session:
        async with session.post("https://oauth2.googleapis.com/token", data=params) as response:
            res = await response.json()
            id_token = res["id_token"]
            access_token = res["access_token"]
            google_user_info = await parse_id_token(id_token, access_token)
            return google_user_info
   
   
async def get_google_public_keys():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://www.googleapis.com/oauth2/v3/certs") as response:
            return await response.json()


         
async def parse_id_token(id_token: str, access_token: str = None) -> GoogleUserInfo:
    options = {}
    if access_token is None:
        options["verify_at_hash"] = False
        
    try:
        data = jwt.decode(
            id_token,
            await get_google_public_keys(),
            audience=settings.GOOGLE_CLIENT_ID,
            issuer="https://accounts.google.com",
            algorithms=["RS256"],
            access_token=access_token,
            options=options
        )
        return GoogleUserInfo(data["sub"], data["email"], data["email_verified"], data["name"])
        
    except JWTError as e:
        logger.warning("JWT decode error", exc_info=True, extra={"id_token": id_token})
        raise e # TODO: change to custom exception


def params_for_get_user_info(code: str) -> dict:
    return {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": "http://localhost:5173/callback",
        "code": code,
        "grant_type": "authorization_code",
    }