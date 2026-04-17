from dataclasses import dataclass


@dataclass
class OauthAccount:
    provider_id: str
    username: str
    email: str
    is_confirmed: bool = False
    
    