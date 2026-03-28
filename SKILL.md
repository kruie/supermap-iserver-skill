---
name: supermap-iserver
description: This skill should be used when the user wants to work with SuperMap iServer GIS server. Covers: (1) Publishing services (map services, data services, analysis services, 3D services); (2) Service management (start/stop/restart, monitoring, caching); (3) REST API operations (service discovery, query, analysis); (4) Security configuration (token authentication, role-based access control, SSL/TLS); (5) Cluster deployment (horizontal scaling, load balancing, failover); (6) Performance optimization (cache strategy, connection pool, thread tuning); (7) Data management (datasource management, data updates); (8) Spatial analysis via services (buffer, overlay, routing, geoprocessing); (9) Monitoring and logging (service status, performance metrics, error logs); (10) iServer administration (backup/restore, license management, system settings).
---

# SuperMap iServer Skill

## 快速开始 - 决策树

**Q: 你想做什么?** (使用下方决策树快速找到合适的操作)

```
服务发布
├─ 发布地图服务?
│   ├─ 从 iDesktopX 发布 → GUI: iDesktopX → 开始 → 发布服务
│   ├─ 从工作空间发布 → REST API: POST /iserver/services
│   └─ 从数据集发布 → scripts/publish_services.py: publish_map_service()
├─ 发布数据服务?
│   ├─ UDB/UDBX 数据源 → scripts/publish_services.py: publish_data_service()
│   └─ 批量发布 → scripts/publish_services.py: batch_publish()
├─ 发布分析服务?
│   ├─ 空间分析服务 → scripts/publish_services.py: publish_analysis_service()
│   └─ 网络分析服务 → scripts/publish_services.py: publish_network_service()
└─ 发布三维服务?
    ├─ S3M 场景 → REST API: POST /iserver/services/3d
    └─ OSGB 倾斜摄影 → scripts/publish_services.py: publish_3d_service()

服务管理
├─ 查看服务列表 → REST API: GET /iserver/services
├─ 服务启停控制 → scripts/service_manager.py
│   ├─ 启动服务 → start_service(service_name)
│   ├─ 停止服务 → stop_service(service_name)
│   ├─ 重启服务 → restart_service(service_name)
│   └─ 查看状态 → get_service_status(service_name)
├─ 服务监控 → scripts/service_monitor.py
│   ├─ 性能监控 → monitor_performance()
│   ├─ 访问统计 → get_access_stats()
│   └─ 错误日志 → get_error_logs()
└─ 缓存管理 → scripts/cache_manager.py
    ├─ 清除缓存 → clear_cache(service_name)
    ├─ 预生成缓存 → pre_generate_cache()
    └─ 缓存策略 → configure_cache_strategy()

REST API 调用
├─ 查询服务 → scripts/rest_client.py: query_service()
├─ 调用地图服务 → scripts/rest_client.py: get_map()
├─ 调用数据服务 → scripts/rest_client.py: query_data()
├─ 调用分析服务 → scripts/rest_client.py: execute_analysis()
└─ 调用三维服务 → scripts/rest_client.py: get_3d_layer()

安全配置
├─ 令牌认证 → references/security.md
├─ 访问控制 → references/security.md
├─ HTTPS/SSL 配置 → references/security.md
└─ 权限管理 → scripts/security_manager.py

集群部署
├─ 集群配置 → references/cluster.md
├─ 负载均衡 → references/cluster.md
├─ 故障转移 → references/cluster.md
└─ 集群监控 → scripts/cluster_manager.py

性能优化
├─ 缓存策略 → references/performance.md
├─ 连接池配置 → references/performance.md
├─ 线程调优 → references/performance.md
└─ 性能监控 → scripts/service_monitor.py
```

---

## 架构说明

SuperMap iServer 自动化采用 **MCP + Skill + REST API 三层架构**:

```
┌─────────────────────────────────────────────────────┐
│           SuperMap iServer 自动化体系                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  MCP Server (iServer 服务层 - 待补充)                 │
│  ├─ 服务发布工具 (地图/数据/分析/3D)                 │
│  ├─ 服务管理工具 (启停/监控/缓存)                    │
│  ├─ REST API 封装                                  │
│  └─ 通过 mcp:// 前缀调用                            │
│                                                      │
│  Skill (智能指导层 - 本文档)                        │
│  ├─ 工作流指导: 服务发布、管理、运维流程             │
│  ├─ 决策支持: 根据需求选择合适的工具和参数           │
│  ├─ 安全指南: 认证、授权、SSL 配置                  │
│  └─ scripts/: REST API 客户端和管理脚本            │
│                                                      │
│  iServer REST API (服务层 - 内置)                   │
│  ├─ 服务管理 API: /iserver/services                 │
│  ├─ 地图服务 API: /iserver/services/map-xxx/rest    │
│  ├─ 数据服务 API: /iserver/services/data-xxx/rest  │
│  ├─ 分析服务 API: /iserver/services/spatialanalyst/rest│
│  └─ 三维服务 API: /iserver/services/3D-xxx/rest    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### MCP vs REST API 何时使用?

| 场景 | 推荐方案 | 原因 |
|------|----------|------|
| 单次服务发布 | **MCP 工具** | 简单快速,无需代码 |
| 批量服务发布 | **Skill scripts** | 灵活控制,支持循环 |
| 服务启停管理 | **Skill scripts** | 状态检查,错误处理 |
| 性能监控 | **Skill scripts** | 持续监控,统计分析 |
| 简单查询 | **REST API** | 直接调用,快速响应 |
| 复杂分析 | **REST API** | 功能完整,参数丰富 |
| 集群部署 | **Skill scripts + REST API** | 多节点协调,状态同步 |

---

## 产品概述

### SuperMap iServer 是什么?

SuperMap iServer 是 SuperMap 产品家族中的 GIS 服务器产品,核心功能包括:

1. **服务发布**: 将 GIS 数据和分析功能发布为标准 Web 服务
2. **服务管理**: 统一管理各类 GIS 服务,提供监控、缓存、安全等功能
3. **REST API**: 提供 RESTful API,支持多语言客户端调用
4. **集群部署**: 支持集群部署和负载均衡,提供高可用性
5. **多协议支持**: 支持 WMS、WMTS、WFS、WPS 等 OGC 标准

### 服务类型

| 服务类型 | 说明 | 典型应用 |
|---------|------|---------|
| **地图服务** | 发布地图为 Web 服务,支持切片、动态渲染 | Web 地图、移动应用 |
| **数据服务** | 发布矢量/栅格数据,支持查询、编辑 | 数据共享、协同编辑 |
| **分析服务** | 发布空间分析工具,支持在线分析 | 空间分析、地理处理 |
| **网络分析服务** | 发布网络分析功能,支持路径规划 | 导航、物流优化 |
| **三维服务** | 发布三维场景、模型、S3M 瓦片 | 三维展示、城市模型 |
| **影像服务** | 发布影像数据,支持动态裁剪 | 影像展示、遥感分析 |

---

## 常见工作流

### 工作流 1: 从 iDesktopX 发布地图服务 (推荐初学者)

**场景**: 将 iDesktopX 中制作的地图发布为 iServer 地图服务

```
步骤 1: 在 iDesktopX 中打开工作空间
  → iDesktopX GUI → 工作空间管理器 → 打开 MyProject.smwu

步骤 2: 配置地图
  → 添加图层、设置样式、配置比例尺

步骤 3: 发布服务
  → 菜单: 开始 → 发布 → 发布 iServer 服务
  → 选择: 地图服务
  → 设置: 服务名称 "map-world"、访问地址 http://localhost:8090
  → 点击: 发布

步骤 4: 验证服务
  → 浏览器访问: http://localhost:8090/iserver/services/map-world/rest
  → 查看: 服务元数据、图层列表、WMS/WMTS 地址

步骤 5: 在客户端调用
  → iClient JavaScript: map = L.supermap.map("map-world")
  → OpenLayers: new ol.layer.Tile({source: new ol.source.TileSuperMap()})
```

---

### 工作流 2: 批量发布数据服务 (自动化)

**场景**: 将多个数据源批量发布为数据服务

```python
# 使用 scripts/publish_services.py
from scripts.publish_services import batch_publish

# 批量发布配置
datasources = [
    {"path": "D:/data/cities.udbx", "name": "data-cities"},
    {"path": "D:/data/roads.udbx", "name": "data-roads"},
    {"path": "D:/data/buildings.udbx", "name": "data-buildings"}
]

# 批量发布
results = batch_publish(
    server_url="http://localhost:8090",
    service_type="data",
    datasources=datasources,
    overwrite=True  # 覆盖已存在服务
)

# 查看发布结果
for service, status in results.items():
    print(f"{service}: {'✓ 成功' if status else '✗ 失败'}")
```

---

### 工作流 3: 调用地图服务 REST API

**场景**: 通过 REST API 获取地图数据

```python
# 使用 scripts/rest_client.py
from scripts.rest_client import iServerClient

# 初始化客户端
client = iServerClient(
    server_url="http://localhost:8090",
    token="your_token"  # 可选,如果启用了令牌认证
)

# 获取地图元数据
map_info = client.get_map("map-world")
print(f"地图名称: {map_info.name}")
print(f"坐标系统: {map_info.prjCoordSys}")
print(f"图层列表: {[layer.name for layer in map_info.layers]}")

# 获取地图图片
map_image = client.get_map_image(
    service_name="map-world",
    bounds=(-180, -90, 180, 90),  # 世界范围
    width=1024,
    height=512
)

# 保存图片
with open("map.png", "wb") as f:
    f.write(map_image)
```

---

### 工作流 4: 服务监控与性能调优

**场景**: 监控服务运行状态,优化性能

```python
# 使用 scripts/service_monitor.py
from scripts.service_monitor import ServiceMonitor

# 创建监控器
monitor = ServiceMonitor(
    server_url="http://localhost:8090",
    token="your_token"
)

# 监控所有服务
for service in ["map-world", "data-cities", "spatialanalyst"]:
    status = monitor.get_service_status(service)
    print(f"{service}:")
    print(f"  状态: {status.state}")  # RUNNING/STOPPED
    print(f"  CPU: {status.cpu_usage}%")
    print(f"  内存: {status.memory_usage}MB")
    print(f"  请求/秒: {status.requests_per_second}")
    print(f"  平均响应时间: {status.avg_response_time}ms")

# 生成性能报告
report = monitor.generate_performance_report(hours=24)
monitor.save_report(report, "performance_report.html")
```

---

### 工作流 5: 配置安全认证

**场景**: 启用令牌认证,保护服务安全

```python
# 使用 scripts/security_manager.py
from scripts.security_manager import SecurityManager

# 创建安全管理器
security = SecurityManager(
    server_url="http://localhost:8090",
    username="admin",
    password="supermap"
)

# 启用令牌认证
security.enable_token_auth(
    token_enabled=True,
    token_expire_hours=24,
    max_token_count=100
)

# 创建用户和角色
security.create_user("analyst", "password123", ["analyst_role"])
security.create_role("analyst_role", permissions=["read"])

# 获取访问令牌
token = security.get_token("analyst", "password123")
print(f"访问令牌: {token}")
```

---

## MCP 工具补充建议

为了方便操作 iServer,建议补充以下 MCP 工具:

| 工具名称 | 功能描述 | 参数 |
|---------|---------|------|
| `publish_map_service` | 发布地图服务 | workspace_path, map_name, service_name |
| `publish_data_service` | 发布数据服务 | datasource_path, service_name |
| `publish_analysis_service` | 发布分析服务 | workspace_path, service_name |
| `start_service` | 启动服务 | service_name |
| `stop_service` | 停止服务 | service_name |
| `get_service_status` | 获取服务状态 | service_name |
| `clear_cache` | 清除缓存 | service_name |
| `get_token` | 获取访问令牌 | username, password |
| `get_map` | 调用地图服务 | service_name, bounds, width, height |
| `query_data` | 调用数据服务 | service_name, dataset_name, filter |

---

## Scripts 工具库

### scripts/publish_services.py

**功能**: 服务发布工具

```python
from scripts.publish_services import (
    publish_map_service, publish_data_service,
    publish_analysis_service, batch_publish
)

# 发布地图服务
publish_map_service(
    workspace_path="D:/data/world.smwu",
    map_name="World",
    service_name="map-world",
    server_url="http://localhost:8090"
)

# 批量发布数据服务
batch_publish(
    server_url="http://localhost:8090",
    service_type="data",
    datasources=[...]
)
```

---

### scripts/service_manager.py

**功能**: 服务管理工具

```python
from scripts.service_manager import ServiceManager

manager = ServiceManager("http://localhost:8090")

# 服务启停
manager.start_service("map-world")
manager.stop_service("data-cities")
manager.restart_service("spatialanalyst")

# 查看状态
status = manager.get_service_status("map-world")
```

---

### scripts/rest_client.py

**功能**: REST API 客户端

```python
from scripts.rest_client import iServerClient

client = iServerClient("http://localhost:8090", token="xxx")

# 调用各种服务
map_data = client.get_map("map-world")
data = client.query_data("data-cities", "Cities")
result = client.execute_analysis("spatialanalyst", "buffer", {...})
```

---

### scripts/service_monitor.py

**功能**: 服务监控工具

```python
from scripts.service_monitor import ServiceMonitor

monitor = ServiceMonitor("http://localhost:8090")

# 性能监控
stats = monitor.monitor_performance()

# 生成报告
report = monitor.generate_performance_report(hours=24)
```

---

### scripts/security_manager.py

**功能**: 安全管理工具

```python
from scripts.security_manager import SecurityManager

security = SecurityManager("http://localhost:8090", "admin", "xxx")

# 令牌认证
token = security.get_token("analyst", "password123")

# 用户管理
security.create_user("user1", "pass123", ["role1"])
```

---

## 参考文档

| 文件 | 内容 |
|------|------|
| `references/rest-api.md` | 完整的 REST API 参考文档 |
| `references/security.md` | 安全配置指南 (令牌认证、访问控制、SSL) |
| `references/cluster.md` | 集群部署指南 (配置、负载均衡、故障转移) |
| `references/performance.md` | 性能优化指南 (缓存、连接池、线程调优) |
| `references/deployment.md` | 部署指南 (安装、配置、备份恢复) |
| `references/monitoring.md` | 监控与日志 (监控指标、日志分析) |

---

## FAQ

**Q: "服务发布失败"错误**  
A: 检查数据源路径是否正确,数据集是否存在,iServer 是否有访问权限。

**Q: "令牌认证失败"错误**  
A: 检查用户名密码是否正确,令牌是否过期,服务是否启用了令牌认证。

**Q: "服务访问慢"问题**  
A: 检查是否启用了缓存,数据量是否过大,是否需要优化数据库查询。

**Q: "集群节点不同步"问题**  
A: 检查集群配置,节点间网络连接,同步间隔设置。

---

## 相关产品

- **SuperMap iDesktopX**: 桌面 GIS 软件,用于地图制作、数据处理
- **SuperMap iServer**: GIS 服务器,用于服务发布和共享
- **SuperMap iClient**: Web 端客户端,用于服务调用和展示
- **SuperMap iObjectsJava/Python**: 开发包,用于二次开发

---

**Skill 版本**: v1.0  
**更新时间**: 2026-03-27  
**适用版本**: SuperMap iServer 11i (2025)
