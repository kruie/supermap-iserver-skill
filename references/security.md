# SuperMap iServer 安全配置指南

## 概述

SuperMap iServer 提供完整的安全机制,包括令牌认证、用户管理、角色权限、SSL/TLS 加密等。

---

## 一、令牌认证

### 1.1 启用令牌认证

令牌认证是推荐的安全认证方式,比基本认证更安全。

**配置位置**: `iserver/etc/iserver-system.xml`

```xml
<security>
  <token>
    <enabled>true</enabled>
    <expireHours>24</expireHours>
    <maxTokenCount>100</maxTokenCount>
  </token>
</security>
```

**参数说明**:
- `enabled`: 是否启用令牌认证
- `expireHours`: 令牌过期时间 (小时)
- `maxTokenCount`: 最大令牌数量

### 1.2 获取令牌

**API**:

```http
POST /iserver/security/token
Content-Type: application/json

{
  "username": "admin",
  "password": "supermap"
}
```

**响应**:

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expireTime": "2026-03-28T22:00:00Z",
  "userId": "admin"
}
```

### 1.3 使用令牌

**方式 1: 查询参数**

```http
GET /iserver/services?token=your_token_string
```

**方式 2: 请求头 (推荐)**

```http
GET /iserver/services
token: your_token_string
```

### 1.4 验证令牌

```http
GET /iserver/security/token/validate?token=your_token_string
```

**响应**:

```json
{
  "valid": true,
  "expireTime": "2026-03-28T22:00:00Z"
}
```

### 1.5 撤销令牌

```http
POST /iserver/security/token/revoke
Content-Type: application/json

{
  "token": "your_token_string"
}
```

---

## 二、用户管理

### 2.1 创建用户

**API**:

```http
POST /iserver/security/users
Content-Type: application/json

{
  "username": "analyst",
  "password": "password123",
  "displayName": "数据分析师",
  "email": "analyst@example.com",
  "roles": ["analyst_role"]
}
```

### 2.2 更新用户

```http
POST /iserver/security/users/{username}
Content-Type: application/json

{
  "displayName": "高级分析师",
  "email": "analyst@example.com",
  "roles": ["analyst_role", "editor_role"]
}
```

### 2.3 删除用户

```http
POST /iserver/security/users/{username}/delete
```

### 2.4 查询用户

```http
GET /iserver/security/users/{username}
```

**响应**:

```json
{
  "username": "analyst",
  "displayName": "数据分析师",
  "email": "analyst@example.com",
  "roles": ["analyst_role"],
  "createTime": "2026-03-27T10:00:00Z"
}
```

### 2.5 列出所有用户

```http
GET /iserver/security/users
```

---

## 三、角色管理

### 3.1 内置角色

iServer 默认提供以下角色:

| 角色名 | 权限 |
|-------|------|
| `ADMIN` | 管理员,所有权限 |
| `SERVICE_PROVIDER` | 服务提供者,可以发布和管理服务 |
| `SERVICE_CONSUMER` | 服务消费者,可以调用服务 |
| `GUEST` | 访客,只读权限 |

### 3.2 创建角色

```http
POST /iserver/security/roles
Content-Type: application/json

{
  "name": "analyst_role",
  "description": "数据分析师角色",
  "permissions": ["read", "query", "analyze"]
}
```

**权限类型**:
- `read`: 读取服务
- `write`: 写入数据
- `query`: 查询数据
- `analyze`: 执行分析
- `publish`: 发布服务
- `manage`: 管理服务
- `admin`: 管理员权限

### 3.3 更新角色

```http
POST /iserver/security/roles/{role_name}
Content-Type: application/json

{
  "description": "高级数据分析师",
  "permissions": ["read", "write", "query", "analyze", "publish"]
}
```

### 3.4 删除角色

```http
POST /iserver/security/roles/{role_name}/delete
```

### 3.5 列出所有角色

```http
GET /iserver/security/roles
```

---

## 四、服务访问控制

### 4.1 设置服务访问控制

```http
POST /iserver/security/accesscontrol
Content-Type: application/json

{
  "serviceName": "map-world",
  "allowedRoles": ["analyst_role", "admin_role"],
  "deniedRoles": []
}
```

### 4.2 获取服务访问控制

```http
GET /iserver/security/accesscontrol?serviceName=map-world
```

**响应**:

```json
{
  "serviceName": "map-world",
  "allowedRoles": ["analyst_role", "admin_role"],
  "deniedRoles": []
}
```

### 4.3 数据集访问控制

```http
POST /iserver/security/dataaccesscontrol
Content-Type: application/json

{
  "datasourceName": "world",
  "datasetName": "Capitals",
  "allowedRoles": ["analyst_role"],
  "deniedRoles": []
}
```

---

## 五、SSL/TLS 配置

### 5.1 生成自签名证书

```bash
# 使用 OpenSSL 生成自签名证书
openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes

# 或生成证书签名请求 (CSR)
openssl req -new -newkey rsa:4096 -keyout server.key -out server.csr
```

### 5.2 配置 SSL

**配置位置**: `iserver/etc/iserver-system.xml`

```xml
<server>
  <ssl>
    <enabled>true</enabled>
    <sslPort>8443</sslPort>
    <keystorePath>/path/to/keystore.jks</keystorePath>
    <keystorePassword>your_password</keystorePassword>
    <keyPassword>your_password</keyPassword>
  </ssl>
</server>
```

**使用 JKS 格式**:

```bash
# 将证书和私钥转换为 JKS 格式
openssl pkcs12 -export -in server.crt -inkey server.key -out server.p12 -name tomcat
keytool -importkeystore -deststorepass your_password -destkeypass your_password -destkeystore keystore.jks -srckeystore server.p12 -srcstoretype PKCS12 -srcstorepass your_password -alias tomcat
```

### 5.3 启用 HTTP 强制跳转 HTTPS

```xml
<security>
  <redirect>
    <enabled>true</enabled>
    <targetUrl>https://your-server:8443</targetUrl>
  </redirect>
</security>
```

### 5.4 测试 SSL 配置

```bash
# 测试 HTTPS 连接
curl -k https://localhost:8443/iserver/services

# 查看证书信息
openssl s_client -connect localhost:8443 -showcerts
```

---

## 六、防火墙配置

### 6.1 Windows 防火墙

```powershell
# 允许 HTTP 端口
New-NetFirewallRule -DisplayName "iServer HTTP" -Direction Inbound -Protocol TCP -LocalPort 8090 -Action Allow

# 允许 HTTPS 端口
New-NetFirewallRule -DisplayName "iServer HTTPS" -Direction Inbound -Protocol TCP -LocalPort 8443 -Action Allow
```

### 6.2 Linux iptables

```bash
# 允许 HTTP 端口
iptables -A INPUT -p tcp --dport 8090 -j ACCEPT

# 允许 HTTPS 端口
iptables -A INPUT -p tcp --dport 8443 -j ACCEPT

# 保存规则
service iptables save
```

### 6.3 Linux firewalld

```bash
# 添加端口
firewall-cmd --permanent --add-port=8090/tcp
firewall-cmd --permanent --add-port=8443/tcp

# 重载防火墙
firewall-cmd --reload
```

---

## 七、常见安全配置场景

### 场景 1: 公网访问 + HTTPS

**需求**: iServer 部署在公网,需要 HTTPS 加密和基本安全控制。

**配置步骤**:

1. 购买 SSL 证书 (Let's Encrypt 免费证书或商业证书)
2. 配置 SSL (参考 5.2 节)
3. 启用令牌认证
4. 创建受限用户角色
5. 设置服务访问控制

**配置示例**:

```xml
<security>
  <token>
    <enabled>true</enabled>
    <expireHours>8</expireHours>
    <maxTokenCount>50</maxTokenCount>
  </token>
  <redirect>
    <enabled>true</enabled>
    <targetUrl>https://your-server:8443</targetUrl>
  </redirect>
</security>

<server>
  <ssl>
    <enabled>true</enabled>
    <sslPort>8443</sslPort>
    <keystorePath>/path/to/keystore.jks</keystorePath>
    <keystorePassword>strong_password</keystorePassword>
  </ssl>
</server>
```

### 场景 2: 内网访问 + 用户权限控制

**需求**: iServer 部署在内网,需要区分不同用户权限。

**配置步骤**:

1. 创建多个用户角色
2. 为不同角色分配不同权限
3. 设置服务访问控制
4. 设置数据集访问控制

**配置示例**:

```python
# 使用 scripts/security_manager.py

# 创建角色
security.create_role(
    name="analyst_role",
    description="数据分析师",
    permissions=["read", "query", "analyze"]
)

security.create_role(
    name="editor_role",
    description="数据编辑",
    permissions=["read", "write", "query"]
)

# 创建用户
security.create_user(
    username="analyst1",
    password="pass123",
    roles=["analyst_role"]
)

security.create_user(
    username="editor1",
    password="pass123",
    roles=["editor_role"]
)

# 设置服务访问控制
security.set_service_access_control(
    service_name="map-world",
    allowed_roles=["analyst_role", "editor_role", "ADMIN"]
)

# 设置数据集访问控制
security.set_dataset_access_control(
    datasource_name="world",
    dataset_name="Capitals",
    allowed_roles=["analyst_role"]
)
```

### 场景 3: 外部系统集成 + API Key

**需求**: 外部系统通过 API 调用 iServer,需要 API Key 机制。

**实现方式**:

1. 为外部系统创建专用用户
2. 生成长期有效的令牌
3. 外部系统使用令牌调用 API

**Python 示例**:

```python
import requests

# 外部系统获取令牌 (登录一次,缓存令牌)
def get_token():
    response = requests.post(
        "http://localhost:8090/iserver/security/token",
        json={
            "username": "external_system",
            "password": "secure_password"
        }
    )
    return response.json()["token"]

# 使用令牌调用 API
TOKEN = get_token()

response = requests.get(
    "http://localhost:8090/iserver/services/map-world/rest/maps/World.json",
    headers={"token": TOKEN}
)
```

---

## 八、安全最佳实践

### 8.1 密码安全

- ✅ 使用强密码 (至少 12 位,包含大小写字母、数字、特殊字符)
- ✅ 定期更换密码
- ✅ 不同用户使用不同密码
- ❌ 不使用默认密码
- ❌ 不在代码中硬编码密码

### 8.2 令牌管理

- ✅ 使用 HTTPS 传输令牌
- ✅ 设置合理的过期时间 (8-24 小时)
- ✅ 限制最大令牌数量
- ✅ 及时撤销不需要的令牌
- ❌ 不在 URL 中传递令牌 (容易泄露)
- ❌ 不将令牌存储在本地文件

### 8.3 访问控制

- ✅ 遵循最小权限原则
- ✅ 为不同角色分配不同权限
- ✅ 定期审查用户和角色
- ✅ 启用服务访问控制
- ❌ 不使用管理员账号进行日常操作

### 8.4 网络安全

- ✅ 使用 HTTPS 加密
- ✅ 配置防火墙规则
- ✅ 限制访问 IP (使用反向代理)
- ✅ 定期更新 iServer 版本
- ❌ 不在公网暴露管理端口

### 8.5 日志监控

- ✅ 启用访问日志
- ✅ 启用错误日志
- ✅ 定期检查异常访问
- ✅ 设置日志告警

---

## 九、安全检查清单

- [ ] 已更改管理员默认密码
- [ ] 已启用令牌认证
- [ ] 已配置 HTTPS (如果是公网)
- [ ] 已创建受限用户角色
- [ ] 已设置服务访问控制
- [ ] 已配置防火墙规则
- [ ] 已启用访问日志
- [ ] 已设置令牌过期时间
- [ ] 已限制最大令牌数量
- [ ] 已定期备份配置

---

## 十、故障排除

### 问题 1: 令牌认证失败

**原因**:
- 令牌过期
- 令牌格式错误
- 令牌被撤销

**解决**:
1. 重新获取令牌
2. 检查令牌是否过期
3. 验证令牌格式

### 问题 2: SSL 证书错误

**原因**:
- 证书过期
- 证书链不完整
- 域名不匹配

**解决**:
1. 更新证书
2. 安装完整证书链
3. 确保证书域名匹配

### 问题 3: 访问被拒绝 (403)

**原因**:
- 权限不足
- 角色配置错误
- 服务访问控制限制

**解决**:
1. 检查用户角色和权限
2. 验证服务访问控制配置
3. 使用管理员账号测试

---

**文档版本**: v1.0
**更新时间**: 2026-03-27
**适用版本**: SuperMap iServer 11i (2025)
