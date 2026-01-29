"""
MySQL数据库访问模块（异步版本）
提供用户信息查询功能
"""
import logging
from typing import Optional, Dict, Any
import aiomysql
from config import settings

logger = logging.getLogger(__name__)


class MySQLClient:
    """MySQL数据库客户端（异步）"""

    def __init__(self):
        """初始化数据库连接池配置"""
        self._pool = None
        self._config = {
            'host': settings.mysql_host,
            'port': settings.mysql_port,
            'user': settings.mysql_user,
            'password': settings.mysql_password,
            'db': settings.mysql_database,
            'charset': 'utf8mb4',
            'autocommit': True,
        }

    async def _get_pool(self):
        """获取或创建连接池"""
        if self._pool is None:
            self._pool = await aiomysql.create_pool(
                minsize=1,
                maxsize=10,
                **self._config
            )
        return self._pool

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        根据user_id查询用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，不存在则返回None
        """
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    sql = "SELECT user_id, user_name, phone, is_active FROM tb_user WHERE user_id = %s"
                    await cursor.execute(sql, (user_id,))
                    result = await cursor.fetchone()
                    return result
        except Exception as e:
            logger.error(f"查询用户信息失败: user_id={user_id}, error={e}")
            return None

    async def get_user_name(self, user_id: str) -> Optional[str]:
        """
        根据user_id查询用户名

        Args:
            user_id: 用户ID

        Returns:
            用户名，不存在则返回None
        """
        user = await self.get_user_by_id(user_id)
        return user['user_name'] if user else None

    async def close(self):
        """关闭连接池"""
        if self._pool:
            self._pool.close()
            await self._pool.wait_closed()
            self._pool = None


# 创建全局MySQL客户端实例
mysql_client = MySQLClient()
