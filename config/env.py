import os
from dataclasses import dataclass

from utils.helper import parseBool


@dataclass(frozen=True)
class Env:
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    PRODUCTION: bool = parseBool(os.getenv("PRODUCTION", "false"))
    DEBUG: bool = parseBool(os.getenv("DEBUG", "true"))
    RELOAD: bool = parseBool(os.getenv("RELOAD", "false"))
    TZ: str = os.getenv("TZ", "Asia/Jakarta")
    WORKERS: int = int(os.getenv("WORKERS", 1))

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    TOKEN_EXPIRES_HOURS: int = int(os.getenv("JWT_EXPIRES_HOURS", 24))
    REFRESH_TOKEN_EXPIRES_HOURS: int = int(os.getenv("REFRESH_TOKEN_EXPIRES_HOURS", 24))
    INITIAL_CUSTOMER_USER_USERNAME: str = os.getenv("INITIAL_CUSTOMER_USER_USERNAME", "")
    INITIAL_CUSTOMER_USER_PASSWORD: str = os.getenv("INITIAL_CUSTOMER_USER_PASSWORD", "")
    INITIAL_SELLER_USER_USERNAME: str = os.getenv("INITIAL_SELLER_USER_USERNAME", "")
    INITIAL_SELLER_USER_PASSWORD: str = os.getenv("INITIAL_SELLER_USER_PASSWORD", "")

    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_NAME: str = os.getenv("MONGODB_NAME", "quickmart")
    GMAIL_SENDER_EMAIL: str = os.getenv("GMAIL_SENDER_EMAIL", "")
    GMAIL_SENDER_PASSWORD: str = os.getenv("GMAIL_SENDER_PASSWORD", "")