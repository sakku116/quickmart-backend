import time
import json
from uuid import uuid4
from datetime import datetime
import random
from babel import Locale
from babel.numbers import get_currency_symbol


def parseBool(source: any) -> bool:
    if str(source).strip().lower() in ["none", 0, "", "false"]:
        return False
    return True


def generateSkip(page: int, limit: int) -> int:
    return (page - 1) * limit


def timeNowEpoch() -> int:
    return int(datetime.utcnow().timestamp())


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

def isExpired(created_at: int, expr_hours: int = None, expr_seconds: int = None) -> bool:
    if not expr_hours and not expr_seconds:
        raise ValueError("Either 'expr_hours' or 'expr_seconds' must be provided.")
    current_time = int(datetime.utcnow().timestamp())  # Get current time in epoch format
    if expr_hours:
        expiration_time = created_at + (
            expr_hours * 3600
        )
    elif expr_seconds:
        expiration_time = created_at + expr_seconds
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

def isCurrencyCodeValid(currency_code: str) -> bool:
    try:
        get_currency_symbol(currency_code)
        return True
    except Exception as e:
        return False