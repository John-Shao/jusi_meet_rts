# Redis 缓存集成说明

本项目已集成 Redis 作为房间数据的持久化存储，支持数据在服务重启后恢复。

## 1. 前置要求

确保你的系统已安装并运行 Redis 服务：

### Windows
```bash
# 使用 Chocolatey 安装
choco install redis-64

# 启动 Redis 服务
redis-server
```

### Linux/Mac
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# 启动 Redis 服务
redis-server
```

## 2. 安装依赖

项目的 `requirements.txt` 已包含 Redis 依赖，运行以下命令安装：

```bash
pip install -r requirements.txt
```

或单独安装 Redis 包：

```bash
pip install redis==5.0.1
```

## 3. 配置 Redis 连接

在 `.env` 文件中配置 Redis 连接信息（已预配置默认值）：

```env
# Redis配置
REDIS_HOST=localhost        # Redis 服务器地址
REDIS_PORT=6379            # Redis 端口
REDIS_DB=0                 # Redis 数据库编号（0-15）
REDIS_PASSWORD=            # Redis 密码（如果有的话）
REDIS_PREFIX=jusi_meet:    # Redis 键前缀，用于区分不同应用的数据
```

### 配置说明

- `REDIS_HOST`: Redis 服务器地址，默认为 `localhost`
- `REDIS_PORT`: Redis 端口，默认为 `6379`
- `REDIS_DB`: Redis 数据库编号，范围 0-15，默认为 `0`
- `REDIS_PASSWORD`: Redis 密码，如果 Redis 没有设置密码则留空
- `REDIS_PREFIX`: 键前缀，所有存储的键都会加上这个前缀，方便管理和区分

## 4. 架构说明

### 数据存储结构

房间数据使用以下 Redis 键结构：

```
jusi_meet:room:{room_id}          # 存储房间基本信息（JSON字符串）
jusi_meet:room:{room_id}:users    # 存储房间用户列表（Hash结构）
```

### 存储策略

- **内存 + Redis 双重存储**: 房间数据同时存储在内存和 Redis 中
  - 内存存储：提供快速访问
  - Redis 存储：提供持久化和跨进程共享

- **自动同步**: 所有房间状态变更（用户进入/离开、设备操作等）都会自动同步到 Redis

- **延迟加载**: 如果内存中没有房间数据，会自动从 Redis 加载

### 核心文件

1. **redis_client.py**
   - `RedisClient` 类：封装所有 Redis 操作
   - 提供房间的增删改查接口
   - 自动处理序列化/反序列化

2. **rts_service.py**
   - 在所有房间操作中自动同步 Redis
   - 支持从 Redis 恢复房间数据

3. **room_model.py** 和 **user_model.py**
   - 添加了 `to_dict()` 和 `from_dict()` 方法
   - 支持对象序列化到 Redis 和从 Redis 反序列化

## 5. 使用示例

### 测试 Redis 连接

```python
from redis_client import redis_client

# 测试连接
if redis_client.ping():
    print("Redis 连接成功!")
else:
    print("Redis 连接失败!")
```

### 查看 Redis 中的数据

使用 Redis CLI 工具查看存储的数据：

```bash
# 连接到 Redis
redis-cli

# 查看所有房间键
KEYS jusi_meet:room:*

# 查看特定房间的信息
GET jusi_meet:room:your_room_id

# 查看房间的用户列表
HGETALL jusi_meet:room:your_room_id:users

# 删除特定房间
DEL jusi_meet:room:your_room_id
DEL jusi_meet:room:your_room_id:users
```

### 手动操作（调试用）

```python
from redis_client import redis_client

# 获取所有房间ID
room_ids = redis_client.get_all_room_ids()
print(f"所有房间: {room_ids}")

# 获取特定房间数据
room_data = redis_client.get_room("room_id")
print(f"房间数据: {room_data}")

# 获取房间用户列表
users_data = redis_client.get_room_users("room_id")
print(f"用户列表: {users_data}")

# 检查房间是否存在
exists = redis_client.exists_room("room_id")
print(f"房间存在: {exists}")
```

## 6. 数据持久化

Redis 默认配置会定期将数据持久化到磁盘：

- **RDB 快照**: 定期保存数据库快照
- **AOF 日志**: 记录每个写操作（可选）

如需调整持久化策略，编辑 Redis 配置文件 `redis.conf`。

## 7. 监控和维护

### 查看 Redis 内存使用

```bash
redis-cli info memory
```

### 清空所有项目数据

```bash
redis-cli
> KEYS jusi_meet:*
> DEL jusi_meet:room:*  # 小心使用！会删除所有房间数据
```

### 设置键的过期时间（可选）

如果希望房间在一定时间后自动清除，可以在 `redis_client.py` 中设置 TTL：

```python
# 设置房间24小时后过期
self._client.expire(key, 86400)  # 86400秒 = 24小时
```

## 8. 故障排查

### 无法连接到 Redis

**症状**: 应用启动时报错 `ConnectionError` 或 `TimeoutError`

**解决方案**:
1. 确认 Redis 服务是否运行: `redis-cli ping` 应返回 `PONG`
2. 检查 `.env` 中的配置是否正确
3. 检查防火墙设置是否阻止了连接

### Redis 数据不同步

**症状**: 服务重启后房间数据丢失

**解决方案**:
1. 检查 Redis 是否正常运行
2. 查看日志确认是否有 Redis 写入错误
3. 使用 `redis-cli` 手动检查数据是否存在

### 内存占用过高

**解决方案**:
1. 定期清理过期房间数据
2. 设置 Redis 内存限制和淘汰策略
3. 监控房间创建和销毁是否正常

## 9. 性能优化建议

1. **连接池**: `redis-py` 默认使用连接池，无需额外配置
2. **批量操作**: 使用 Pipeline 进行批量写入（已在代码中实现）
3. **合理设置过期时间**: 避免长期无用的房间数据占用内存
4. **监控慢查询**: 使用 `SLOWLOG` 命令监控慢查询

## 10. 生产环境建议

1. **高可用部署**: 使用 Redis Sentinel 或 Redis Cluster
2. **备份策略**: 定期备份 RDB 文件
3. **监控**: 使用 Redis 监控工具（如 RedisInsight, Prometheus + Grafana）
4. **安全**: 设置强密码，绑定特定 IP，使用 SSL/TLS
5. **资源限制**: 设置 `maxmemory` 和合适的淘汰策略

---

如有问题，请查看日志或联系技术支持。
