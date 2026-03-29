# SuperMap iServer 性能优化指南

## 1. 概述

本文档提供 SuperMap iServer 的性能优化策略和最佳实践，帮助管理员提升服务响应速度、吞吐量和资源利用率。

---

## 2. 系统资源配置

### 2.1 JVM 内存配置

iServer 基于 Java 运行，合理的 JVM 内存配置是性能基础：

```bash
# 修改 %ISERVER_HOME%/bin/catalina.bat（Windows）或 catalina.sh（Linux）
# 建议配置（16GB 内存服务器）：
set JAVA_OPTS=-Xms4g -Xmx8g -XX:MaxMetaspaceSize=512m -XX:+UseG1GC
```

| 服务器内存 | 建议初始堆 | 建议最大堆 | Metaspace |
|-----------|-----------|-----------|-----------|
| 8 GB | 2 GB | 4 GB | 256 MB |
| 16 GB | 4 GB | 8 GB | 512 MB |
| 32 GB | 8 GB | 16 GB | 512 MB |
| 64 GB | 16 GB | 32 GB | 1024 MB |

### 2.2 CPU 配置

- **最低要求**：4 核
- **推荐配置**：8 核以上
- **高并发场景**：16 核以上
- **GPU 加速**：支持 CUDA 的显卡可加速三维渲染和影像处理

### 2.3 磁盘配置

| 场景 | 推荐磁盘类型 | 最低 IOPS |
|------|-------------|-----------|
| 开发/测试 | SSD | 1000 |
| 生产（轻量） | SSD | 3000 |
| 生产（高并发） | NVMe SSD | 10000+ |

---

## 3. 服务缓存优化

### 3.1 地图缓存

地图缓存是提升地图服务性能最有效的方式：

```python
# 预生成缓存策略
# 1. 确定缓存比例尺级别
# 2. 设置合适的切片大小（推荐 256×256 或 512×512）
# 3. 分区域预生成，避免一次性生成全量缓存

# 通过 REST API 触发缓存预生成
import requests

response = requests.post(
    "http://localhost:8090/iserver/manager/precache/mapName.json",
    json={
        "scale": 1e-4,
        "bounds": "116.0,39.0,117.0,40.0",
        "tileSize": 256
    },
    headers={"token": "your_token"}
)
```

### 3.2 缓存策略选择

| 缓存类型 | 适用场景 | 切片大小 | 格式 |
|---------|---------|---------|------|
| 地图缓存 | 地图浏览服务 | 256/512 | PNG/WebP |
| 影像缓存 | 影像数据服务 | 256/512 | PNG/JPEG |
| 矢量缓存 | 矢量瓦片服务 | 512 | MVT/PBF |

### 3.3 缓存清除策略

- **定时清除**：设置缓存过期时间，自动清理旧缓存
- **手动清除**：数据更新后手动清除相关区域的缓存
- **增量更新**：只更新变化区域，避免全量重建

```python
# 清除指定服务的缓存
response = requests.post(
    "http://localhost:8090/iserver/manager/clearcache/mapName.json",
    json={"cacheType": "all"},
    headers={"token": "your_token"}
)
```

---

## 4. 连接池优化

### 4.1 数据库连接池

```xml
<!-- 在 %ISERVER_HOME%/webapps/iserver/WEB-INF/iserver.xml 中配置 -->
<connectionPool>
    <maxActive>100</maxActive>
    <maxIdle>20</maxIdle>
    <minIdle>5</minIdle>
    <maxWait>30000</maxWait>
    <testOnBorrow>true</testOnBorrow>
</connectionPool>
```

### 4.2 HTTP 连接池

```xml
<!-- HTTP 请求连接池配置 -->
<httpClient>
    <maxTotalConnections>200</maxTotalConnections>
    <defaultMaxPerRoute>50</defaultMaxPerRoute>
    <connectionTimeout>30000</connectionTimeout>
    <socketTimeout>60000</socketTimeout>
</httpClient>
```

---

## 5. 数据源优化

### 5.1 空间索引

确保所有数据集已建立空间索引：

```python
# 检查空间索引
# 通过 iDesktopX 打开数据源 → 右键数据集 → 属性 → 索引信息
# 或通过 SQL 查询性能来判断是否需要索引
```

### 5.2 数据源连接

- **本地数据源**（UDBX）性能最佳
- **数据库数据源**（PostgreSQL + PostGIS）适合多用户并发
- **文件数据源**（Shapefile）仅适合小数据量

### 5.3 数据量建议

| 操作类型 | 建议最大要素数 | 超出建议 |
|---------|-------------|---------|
| 地图渲染 | 50 万/图层 | 分级显示 + 缓存 |
| 空间查询 | 100 万 | 建立空间索引 |
| 缓冲区分析 | 50 万 | 分区域处理 |
| 叠加分析 | 30 万 | 预处理简化 |

---

## 6. 服务配置优化

### 6.1 Worker 线程配置

```xml
<!-- 在 iserver.xml 中配置 -->
<threadPool>
    <corePoolSize>20</corePoolSize>
    <maxPoolSize>100</maxPoolSize>
    <queueCapacity>500</queueCapacity>
</threadPool>
```

### 6.2 压缩配置

```xml
<!-- 启用 GZIP 压缩减少网络传输 -->
<compression>
    <enabled>true</enabled>
    <mimeTypes>application/json,application/xml,text/html,text/plain</mimeTypes>
    <minResponseSize>1024</minResponseSize>
</compression>
```

### 6.3 安全优化（不要影响性能）

| 配置 | 建议 |
|------|------|
| HTTPS | 生产环境必须启用，使用 TLS 1.2+ |
| Token 验证 | 启用，设置合理的过期时间 |
| CORS | 严格限制允许的域名 |
| IP 白名单 | 生产环境建议开启 |

---

## 7. 监控与诊断

### 7.1 性能监控指标

| 指标 | 健康范围 | 告警阈值 |
|------|---------|---------|
| 平均响应时间 | < 200ms | > 1000ms |
| QPS | 视场景而定 | 突降 50% |
| JVM 堆使用率 | < 75% | > 90% |
| 线程数 | < 200 | > 400 |
| 磁盘 I/O | < 80% | > 95% |

### 7.2 使用 JMX 监控 JVM

```bash
# 启动 JMX 远程监控
set JAVA_OPTS=%JAVA_OPTS% -Dcom.sun.management.jmxremote
set JAVA_OPTS=%JAVA_OPTS% -Dcom.sun.management.jmxremote.port=9010
set JAVA_OPTS=%JAVA_OPTS% -Dcom.sun.management.jmxremote.authenticate=false
set JAVA_OPTS=%JAVA_OPTS% -Dcom.sun.management.jmxremote.ssl=false

# 使用 VisualVM 或 JConsole 连接
# jvisualvm 或 jconsole localhost:9010
```

### 7.3 REST API 监控

```python
import requests

# 获取服务状态
response = requests.get(
    "http://localhost:8090/iserver/manager/services.json",
    headers={"token": "your_token"}
)
services = response.json()

for service in services:
    name = service.get("name", "unknown")
    # 检查各服务状态
    status = requests.get(
        f"http://localhost:8090/iserver/manager/services/{name}.json",
        headers={"token": "your_token"}
    )
    print(f"服务: {name}, 状态: {status.json()}")
```

---

## 8. 集群性能优化

### 8.1 负载均衡

- **Nginx 反向代理**：配置 upstream 轮询
- **会话保持**：使用 ip_hash 或 sticky session
- **健康检查**：配置 max_fails 和 fail_timeout

```nginx
upstream iserver_cluster {
    ip_hash;
    server 192.168.1.101:8090 max_fails=3 fail_timeout=30s;
    server 192.168.1.102:8090 max_fails=3 fail_timeout=30s;
    server 192.168.1.103:8090 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name iserver.example.com;
    
    location / {
        proxy_pass http://iserver_cluster;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 8.2 集群注意事项

- 所有节点使用相同版本
- 共享存储配置统一
- 时钟同步（NTP）
- 集群节点数建议 2-4 个

---

## 9. 常见性能问题排查

### 9.1 服务响应慢

1. 检查数据源是否建立了空间索引
2. 检查地图缓存是否已预生成
3. 检查 JVM 内存是否充足
4. 检查磁盘 I/O 是否达到瓶颈

### 9.2 内存溢出（OOM）

1. 检查 -Xmx 设置是否合理
2. 检查是否有内存泄漏
3. 导出 heap dump 分析：`jmap -dump:format=b,file=heap.hprof <pid>`
4. 检查是否有过大的查询返回结果

### 9.3 高并发卡顿

1. 增加线程池大小
2. 启用连接池
3. 启用 GZIP 压缩
4. 考虑增加集群节点

---

## 10. 性能优化清单

- [ ] JVM 内存参数已优化
- [ ] 地图缓存已预生成
- [ ] 空间索引已建立
- [ ] 数据库连接池已配置
- [ ] GZIP 压缩已启用
- [ ] HTTPS/TLS 已配置
- [ ] 监控告警已设置
- [ ] 集群负载均衡已配置（如适用）
- [ ] 定期清理日志和临时文件
- [ ] 服务定期重启策略已制定
