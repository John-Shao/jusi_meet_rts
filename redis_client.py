import json
import redis
from typing import Dict, Optional, Any
from config import settings


class RedisClient:
    """Redis客户端管理类，用于管理房间数据的存储和检索"""

    def __init__(self):
        """初始化Redis连接"""
        self._client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,  # 自动解码为字符串
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        self._prefix = settings.redis_prefix

    def _get_room_key(self, room_id: str) -> str:
        """生成房间的Redis键"""
        return f"{self._prefix}room:{room_id}"

    def _get_users_key(self, room_id: str) -> str:
        """生成房间用户列表的Redis键"""
        return f"{self._prefix}room:{room_id}:users"

    def set_room(self, room_id: str, room_data: Dict[str, Any]) -> None:
        """
        保存房间信息到Redis

        Args:
            room_id: 房间ID
            room_data: 房间数据字典
        """
        key = self._get_room_key(room_id)
        self._client.set(key, json.dumps(room_data, ensure_ascii=False))

    def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        从Redis获取房间信息

        Args:
            room_id: 房间ID

        Returns:
            房间数据字典，如果不存在则返回None
        """
        key = self._get_room_key(room_id)
        data = self._client.get(key)
        if data:
            return json.loads(data)
        return None

    def delete_room(self, room_id: str) -> None:
        """
        删除房间信息

        Args:
            room_id: 房间ID
        """
        room_key = self._get_room_key(room_id)
        users_key = self._get_users_key(room_id)
        self._client.delete(room_key, users_key)

    def exists_room(self, room_id: str) -> bool:
        """
        检查房间是否存在

        Args:
            room_id: 房间ID

        Returns:
            房间是否存在
        """
        key = self._get_room_key(room_id)
        return self._client.exists(key) > 0

    def set_room_users(self, room_id: str, users_data: Dict[str, Dict[str, Any]]) -> None:
        """
        保存房间用户列表到Redis

        Args:
            room_id: 房间ID
            users_data: 用户数据字典，格式为 {user_id: user_dict}
        """
        key = self._get_users_key(room_id)
        # 使用hash存储，每个用户ID作为field，用户数据作为value
        if users_data:
            pipeline = self._client.pipeline()
            pipeline.delete(key)  # 先清空
            for user_id, user_dict in users_data.items():
                pipeline.hset(key, user_id, json.dumps(user_dict, ensure_ascii=False))
            pipeline.execute()
        else:
            self._client.delete(key)

    def get_room_users(self, room_id: str) -> Dict[str, Dict[str, Any]]:
        """
        从Redis获取房间用户列表

        Args:
            room_id: 房间ID

        Returns:
            用户数据字典，格式为 {user_id: user_dict}
        """
        key = self._get_users_key(room_id)
        users_data = self._client.hgetall(key)
        if users_data:
            return {
                user_id: json.loads(user_json)
                for user_id, user_json in users_data.items()
            }
        return {}

    def get_room_user(self, room_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        获取房间内的单个用户数据

        Args:
            room_id: 房间ID
            user_id: 用户ID

        Returns:
            用户数据字典，如果不存在则返回None
        """
        key = self._get_users_key(room_id)
        user_json = self._client.hget(key, user_id)
        if user_json:
            return json.loads(user_json)
        return None

    def set_room_user(self, room_id: str, user_id: str, user_data: Dict[str, Any]) -> None:
        """
        设置/更新房间内的单个用户数据

        Args:
            room_id: 房间ID
            user_id: 用户ID
            user_data: 用户数据字典
        """
        key = self._get_users_key(room_id)
        self._client.hset(key, user_id, json.dumps(user_data, ensure_ascii=False))

    def add_room_user(self, room_id: str, user_id: str, user_data: Dict[str, Any]) -> None:
        """
        添加用户到房间（别名方法，实际调用set_room_user）

        Args:
            room_id: 房间ID
            user_id: 用户ID
            user_data: 用户数据字典
        """
        self.set_room_user(room_id, user_id, user_data)

    def remove_room_user(self, room_id: str, user_id: str) -> None:
        """
        从房间移除用户

        Args:
            room_id: 房间ID
            user_id: 用户ID
        """
        key = self._get_users_key(room_id)
        self._client.hdel(key, user_id)

    def get_room_user_ids(self, room_id: str) -> list[str]:
        """
        获取房间内所有用户ID列表

        Args:
            room_id: 房间ID

        Returns:
            用户ID列表
        """
        key = self._get_users_key(room_id)
        return list(self._client.hkeys(key))

    def get_room_user_count(self, room_id: str) -> int:
        """
        获取房间内用户数量

        Args:
            room_id: 房间ID

        Returns:
            用户数量
        """
        key = self._get_users_key(room_id)
        return self._client.hlen(key)

    def get_all_room_ids(self) -> list[str]:
        """
        获取所有房间ID

        Returns:
            房间ID列表
        """
        pattern = f"{self._prefix}room:*"
        keys = self._client.keys(pattern)
        # 提取room_id，过滤掉users键
        room_ids = []
        for key in keys:
            if not key.endswith(":users"):
                # 提取 "jusi_meet:room:{room_id}" 中的 room_id
                room_id = key.replace(f"{self._prefix}room:", "")
                room_ids.append(room_id)
        return room_ids

    def ping(self) -> bool:
        """
        测试Redis连接是否正常

        Returns:
            连接是否正常
        """
        try:
            return self._client.ping()
        except Exception:
            return False

    def close(self) -> None:
        """关闭Redis连接"""
        self._client.close()


# 创建全局Redis客户端实例
redis_client = RedisClient()
