import uuid
import json
import time
from typing import Dict, Any
from config import settings
from access_token import AccessToken, PrivSubscribeStream, PrivPublishStream


def generate_token(user_id: str, room_id: str) -> str:
    atobj = AccessToken(settings.rtc_app_id, settings.rtc_app_key, room_id, user_id)
    atobj.add_privilege(PrivSubscribeStream, 0)
    atobj.add_privilege(PrivPublishStream, int(time.time()) + settings.token_expire_ts)
    atobj.expire_time(int(time.time()) + settings.token_expire_ts)  # TODO: 复用优化，将token放在redis中，设定过期时间
    return atobj.serialize()

def current_timestamp_s() -> int:
    """获取当前时间戳"""
    return int(time.time())

def current_timestamp_ms() -> int:
    """获取当前时间戳"""
    return int(time.time() * 1000)
