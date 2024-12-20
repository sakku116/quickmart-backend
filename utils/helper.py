import json
import mimetypes
import random
import time
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from babel import Locale
from typing import Optional
from babel.numbers import get_currency_symbol, format_currency


def parseBool(source: any) -> bool:
    if str(source).strip().lower() in ["none", 0, "", "false"]:
        return False
    return True


def generateSkip(page: int, limit: int) -> int:
    return (page - 1) * limit


def timeNowEpoch() -> int:
    return int(datetime.now(timezone.utc).timestamp())


def timeNow() -> datetime:
    return datetime.now(timezone.utc)


def prettyJson(data: any) -> str:
    return json.dumps(data, indent=4)


def limitString(input: str, limit: int = 200) -> str:
    if len(input) > limit:
        return f"{input[:limit]}... ({len(input) - limit} chars left)"
    return input


def generateUUID4() -> str:
    return str(uuid4())


def generateRandomNumber(length: int = 10) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


def isExpired(
    created_at: datetime, expr_hours: int = None, expr_seconds: int = None
) -> bool:
    if not expr_hours and not expr_seconds:
        raise ValueError("Either 'expr_hours' or 'expr_seconds' must be provided.")
    current_time = int(
        datetime.now(timezone.utc).timestamp()
    )  # Get current time in epoch format
    if expr_hours:
        expiration_time = created_at + timedelta(hours=expr_hours)
    if expr_seconds:
        expiration_time = created_at + timedelta(seconds=expr_seconds)
    return current_time > expiration_time

def isPasswordValid(password: str, length: int = 6) -> bool:
    if len(password) < length:
        return False

    if " " in password:
        return False

    return True


def isLanguageCodeValid(language_code: str) -> bool:
    try:
        Locale.parse(language_code)
        return True
    except Exception as e:
        return False


def isCurrencyCodeValid(currency_code: str, locale: Optional[str] = None) -> bool:
    try:
        get_currency_symbol(currency_code, locale=Locale(locale))
        return True
    except Exception as e:
        return False


def getMimeType(string: str) -> str:
    try:
        return mimetypes.guess_type(string)[0]
    except Exception as e:
        return ""


def localizePrice(price: float, currency_code: str, language_code: str) -> str:
    try:
        locale = Locale(language_code)
        return format_currency(price, currency_code, locale=locale)
    except Exception as e:
        return ""


def isImage(filename: str) -> bool:
    mimetype = getMimeType(filename)
    if mimetype and mimetype.startswith("image"):
        return True
    return False
