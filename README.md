# SuperMap iServer Skill

基于 SuperMap iServer REST API 的 GIS 服务器管理自动化 Skill。

## 简介

本 Skill 为 WorkBuddy/Claude 提供 SuperMap iServer 自动化运维能力，涵盖服务发布、服务管理、性能监控、安全配置、集群管理等功能。

## 功能

### 服务发布
- 地图服务（WMS、WMTS）
- 数据服务（WFS）
- 空间分析服务
- 三维服务（S3M、REST 3D）
- 批量发布

### 服务管理
- 服务启停、重启
- 服务状态查询
- 缓存管理
- 服务配置修改

### 服务监控
- 性能监控（响应时间、QPS）
- 访问统计
- 错误日志分析
- HTML 报告生成

### 安全管理
- 令牌认证（Token）
- 用户与角色管理
- SSL/HTTPS 配置
- 访问控制（IP 白名单/黑名单）

### 缓存管理
- 缓存清除
- 缓存预生成
- 缓存策略配置
- 缓存统计

### 集群管理
- 集群健康检查
- 滚动重启
- 持续监控

## 依赖

### 无需 MCP 服务器
本 Skill 基于 REST API，不依赖 MCP 服务器。

### Python 库
- requests（HTTP 客户端）
- pandas（数据分析）
- beautifulsoup4（HTML 解析，可选）

### 软件
- SuperMap iServer 11i/12i

## 安装

```bash
# 克隆 Skill 到用户级目录
git clone https://github.com/kruie/supermap-iserver-skill.git ~/.workbuddy/skills/
```

## 配置

在使用前需要配置 iServer 连接信息：

```python
# 在 scripts/rest_client.py 中配置
ISERVER_HOST = "localhost"
ISERVER_PORT = 8090
ISERVER_USER = "admin"
ISERVER_PASSWORD = "password"
```

## 使用

加载 Skill 后，可以直接在对话中自然语言描述 iServer 管理任务：

```
"帮我发布一个地图服务"
"查询所有服务的运行状态"
"清除所有服务的缓存"
"监控 iServer 性能并生成报告"
```

## 目录结构

```
supermap-iserver-skill/
├── SKILL.md              # Skill 主文档
├── scripts/              # 脚本工具
│   ├── rest_client.py    # REST API 客户端
│   ├── service_manager.py    # 服务管理
│   ├── publish_services.py    # 服务发布
│   ├── service_monitor.py     # 服务监控
│   ├── security_manager.py    # 安全管理
│   ├── cache_manager.py       # 缓存管理
│   └── cluster_manager.py     # 集群管理
├── references/           # 参考文档
│   ├── rest-api.md       # REST API 参考
│   ├── security.md       # 安全配置
│   ├── cluster.md        # 集群部署
│   ├── performance.md    # 性能优化
│   ├── deployment.md     # 部署指南
│   └── monitoring.md     # 监控指南
└── README.md
```

## 文档

详细使用指南请查看 `SKILL.md`：

- **决策树**: 指导如何选择合适的工具
- **工作流**: 5 个常见任务的标准流程
- **FAQ**: 常见问题解答

## REST API 覆盖

- **地图服务**: 地图资源查询、图层查询、视图查询
- **数据服务**: 数据源、数据集查询
- **分析服务**: 缓冲区、叠加分析、网络分析、路径分析
- **OGC 服务**: WMS、WMTS、WFS
- **三维服务**: S3M、三维场景、三维分析

## 许可证

MIT License

## 作者

kruie

## 相关项目

- [supermap-mcp-server](https://github.com/kruie/supermap-mcp-server) - MCP 服务器
- [supermap-idesktop-skill](https://github.com/kruie/supermap-idesktop-skill) - iDesktopX Skill
