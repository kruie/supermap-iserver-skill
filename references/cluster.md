# SuperMap iServer 集群部署指南

## 概述

SuperMap iServer 支持集群部署,通过多个 iServer 节点协同工作,实现高可用、负载均衡、横向扩展。

---

## 一、集群架构

### 1.1 集群类型

**垂直扩展 (Scale Up)**:
- 升级单台服务器配置
- 增加 CPU、内存、磁盘
- 适合小型应用

**水平扩展 (Scale Out)**:
- 增加服务器节点数量
- 负载均衡分配请求
- 适合大型应用

### 1.2 集群拓扑

```
                    [负载均衡器 Nginx]
                           |
        +------------------+------------------+
        |                  |                  |
  [iServer 节点 1]   [iServer 节点 2]   [iServer 节点 3]
        |                  |                  |
        +------------------+------------------+
                           |
                    [共享存储/数据库]
```

---

## 二、集群配置

### 2.1 配置共享存储

iServer 集群需要共享以下资源:

1. **工作空间**: 存储地图和数据源配置
2. **服务配置**: 存储服务发布配置
3. **缓存**: 存储地图缓存 (可选,也可独立存储)

**共享存储方案**:

| 方案 | 优点 | 缺点 |
|------|------|------|
| NFS | 配置简单 | 性能一般 |
| CIFS (SMB) | Windows 原生 | Linux 支持一般 |
| 数据库 | 性能好 | 配置复杂 |
| 对象存储 (S3) | 扩展性好 | 需要额外服务 |

### 2.2 配置 NFS 共享存储

**服务器端 (存储服务器)**:

```bash
# 安装 NFS
sudo apt-get install nfs-kernel-server

# 创建共享目录
sudo mkdir -p /data/iserver
sudo chown nobody:nogroup /data/iserver
sudo chmod 777 /data/iserver

# 配置 NFS 共享
echo "/data/iserver 192.168.1.0/24(rw,sync,no_subtree_check)" | sudo tee -a /etc/exports

# 重启 NFS 服务
sudo systemctl restart nfs-kernel-server
```

**客户端 (iServer 节点)**:

```bash
# 安装 NFS 客户端
sudo apt-get install nfs-common

# 创建挂载点
sudo mkdir -p /mnt/iserver

# 挂载 NFS
sudo mount -t nfs 192.168.1.100:/data/iserver /mnt/iserver

# 开机自动挂载
echo "192.168.1.100:/data/iserver /mnt/iserver nfs defaults 0 0" | sudo tee -a /etc/fstab
```

### 2.3 配置 iServer 使用共享存储

**配置位置**: `iserver/etc/iserver-system.xml`

```xml
<server>
  <workspace>
    <outputPath>/mnt/iserver/workspaces</outputPath>
  </workspace>
  <data>
    <outputPath>/mnt/iserver/data</outputPath>
  </data>
  <cache>
    <outputPath>/mnt/iserver/cache</outputPath>
  </cache>
</server>
```

### 2.4 配置集群节点

每个 iServer 节点需要:

1. 安装相同版本的 iServer
2. 使用相同的共享存储路径
3. 配置相同的端口 (8090, 8443)
4. 配置相同的令牌认证 (如果启用)

**示例配置**:

```xml
<!-- iserver/etc/iserver-system.xml -->
<server>
  <name>iServer-Node1</name>
  <host>192.168.1.101</host>
  <port>8090</port>
  <sslPort>8443</sslPort>
</server>

<!-- 节点 2 -->
<server>
  <name>iServer-Node2</name>
  <host>192.168.1.102</host>
  <port>8090</port>
  <sslPort>8443</sslPort>
</server>
```

---

## 三、负载均衡配置

### 3.1 使用 Nginx 负载均衡

**安装 Nginx**:

```bash
sudo apt-get install nginx
```

**配置 Nginx**:

```nginx
# /etc/nginx/conf.d/iserver.conf

upstream iserver_cluster {
    # 负载均衡算法
    least_conn;  # 最少连接

    # 集群节点
    server 192.168.1.101:8090 weight=1 max_fails=3 fail_timeout=30s;
    server 192.168.1.102:8090 weight=1 max_fails=3 fail_timeout=30s;
    server 192.168.1.103:8090 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name iserver.example.com;

    # HTTP 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name iserver.example.com;

    # SSL 证书配置
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 代理 iServer
    location / {
        proxy_pass http://iserver_cluster;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # 健康检查
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

**负载均衡算法**:

| 算法 | 说明 | 适用场景 |
|------|------|---------|
| `round_robin` (默认) | 轮询 | 请求量均匀 |
| `least_conn` | 最少连接 | 请求处理时间差异大 |
| `ip_hash` | IP 哈希 | 需要会话保持 |
| `hash $request_uri` | URI 哈希 | 缓存友好 |

### 3.2 使用 HAProxy 负载均衡

**安装 HAProxy**:

```bash
sudo apt-get install haproxy
```

**配置 HAProxy**:

```haproxy
# /etc/haproxy/haproxy.cfg

global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    maxconn 4000

defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

frontend iserver_http
    bind *:80
    default_backend iserver_cluster

frontend iserver_https
    bind *:443 ssl crt /etc/haproxy/certs/iserver.pem
    default_backend iserver_cluster

backend iserver_cluster
    balance leastconn
    option httpchk GET /iserver/services
    server node1 192.168.1.101:8090 check
    server node2 192.168.1.102:8090 check
    server node3 192.168.1.103:8090 check

listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 10s
```

---

## 四、故障转移

### 4.1 主备模式

**架构**:
- 主节点: 处理所有请求
- 备节点: 待命,不处理请求
- 故障转移: 主节点故障时,备节点接管

**配置 Keepalived**:

```bash
# 安装 Keepalived
sudo apt-get install keepalived
```

**主节点配置**:

```conf
# /etc/keepalived/keepalived.conf

vrrp_script check_iserver {
    script "curl -f http://localhost:8090/iserver/services || exit 1"
    interval 2
    weight -20
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 100
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass 1234
    }

    virtual_ipaddress {
        192.168.1.100
    }

    track_script {
        check_iserver
    }
}
```

**备节点配置**:

```conf
vrrp_instance VI_1 {
    state BACKUP
    interface eth0
    virtual_router_id 51
    priority 90
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass 1234
    }

    virtual_ipaddress {
        192.168.1.100
    }
}
```

### 4.2 集群健康检查

**Nginx 健康检查**:

```nginx
upstream iserver_cluster {
    server 192.168.1.101:8090 max_fails=3 fail_timeout=30s;
    server 192.168.1.102:8090 max_fails=3 fail_timeout=30s;
    server 192.168.1.103:8090 max_fails=3 fail_timeout=30s;
}
```

**自定义健康检查脚本**:

```bash
#!/bin/bash
# health_check.sh

SERVERS=("192.168.1.101:8090" "192.168.1.102:8090" "192.168.1.103:8090")

for server in "${SERVERS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" http://$server/iserver/services)
    if [ $response -eq 200 ]; then
        echo "$server: OK"
    else
        echo "$server: FAIL (HTTP $response)"
        # 发送告警
        # /usr/bin/send_alert.sh "$server is down"
    fi
done
```

---

## 五、集群管理

### 5.1 集群监控

**监控指标**:

- 节点状态 (运行/停止)
- 请求数量/响应时间
- CPU/内存使用率
- 磁盘使用率
- 缓存命中率

**监控工具**:

- Prometheus + Grafana
- Zabbix
- Nagios

### 5.2 集群扩容

**步骤**:

1. 准备新服务器
2. 安装 iServer
3. 配置共享存储
4. 配置 iServer
5. 加入负载均衡
6. 验证服务

**示例**:

```bash
# 1. 安装 iServer (在新节点)
./SuperMap_iServer_11i_Linux64.bin

# 2. 配置共享存储
sudo mkdir -p /mnt/iserver
sudo mount -t nfs 192.168.1.100:/data/iserver /mnt/iserver

# 3. 配置 iServer
# 编辑 iserver/etc/iserver-system.xml

# 4. 加入负载均衡
# 编辑 Nginx 配置,添加新节点
sudo systemctl reload nginx
```

### 5.3 集群缩容

**步骤**:

1. 从负载均衡移除节点
2. 停止 iServer 服务
3. 清理配置 (可选)
4. 卸载 iServer (可选)

**示例**:

```bash
# 1. 从负载均衡移除 (注释掉节点配置)
sudo vim /etc/nginx/conf.d/iserver.conf
sudo systemctl reload nginx

# 2. 停止 iServer
sudo systemctl stop iserver

# 3. 检查集群状态
curl http://iserver.example.com/iserver/services
```

---

## 六、常见场景

### 场景 1: 3 节点生产集群

**需求**:
- 3 个 iServer 节点
- 1 个负载均衡器 (Nginx)
- 1 个共享存储 (NFS)
- 高可用

**配置**:

| 服务器 | IP | 角色 |
|-------|---|------|
| lb-01 | 192.168.1.100 | 负载均衡 |
| iserver-01 | 192.168.1.101 | iServer 节点 |
| iserver-02 | 192.168.1.102 | iServer 节点 |
| iserver-03 | 192.168.1.103 | iServer 节点 |
| storage-01 | 192.168.1.200 | 共享存储 (NFS) |

**步骤**:

1. 配置 NFS 共享存储
2. 安装 3 个 iServer 节点
3. 配置 Nginx 负载均衡
4. 配置防火墙规则
5. 测试集群功能

### 场景 2: 2 节点主备集群

**需求**:
- 1 个主节点
- 1 个备节点
- 故障自动转移

**配置**:

| 服务器 | IP | 角色 |
|-------|---|------|
| iserver-primary | 192.168.1.101 | 主节点 (MASTER) |
| iserver-backup | 192.168.1.102 | 备节点 (BACKUP) |
| VIP | 192.168.1.100 | 虚拟 IP |

**步骤**:

1. 配置共享存储 (NFS)
2. 配置 Keepalived
3. 配置主备节点
4. 测试故障转移

---

## 七、最佳实践

### 7.1 共享存储

- ✅ 使用高性能存储 (SSD)
- ✅ 配置网络优化 (千兆/万兆)
- ✅ 定期备份
- ❌ 不使用本地存储 (会导致数据不一致)

### 7.2 负载均衡

- ✅ 使用 HTTPS 终止
- ✅ 配置健康检查
- ✅ 设置合理的超时时间
- ❌ 不使用单一负载均衡 (单点故障)

### 7.3 故障转移

- ✅ 配置自动故障转移
- ✅ 定期测试故障转移
- ✅ 设置告警通知
- ❌ 不依赖手动切换

### 7.4 监控告警

- ✅ 监控所有节点
- ✅ 设置告警阈值
- ✅ 定期检查日志
- ❌ 不忽略告警

---

## 八、故障排除

### 问题 1: 节点无法加入集群

**原因**:
- 共享存储未挂载
- 网络不通
- 配置不一致

**解决**:
1. 检查共享存储挂载
2. 检查网络连接
3. 对比配置文件

### 问题 2: 数据不一致

**原因**:
- 共享存储配置错误
- 多个节点写入同一资源

**解决**:
1. 检查共享存储配置
2. 确保共享存储正确挂载
3. 检查锁机制

### 问题 3: 负载均衡不均匀

**原因**:
- 负载均衡算法不当
- 节点性能差异大

**解决**:
1. 调整负载均衡算法
2. 调整节点权重
3. 检查节点性能

---

**文档版本**: v1.0
**更新时间**: 2026-03-27
**适用版本**: SuperMap iServer 11i (2025)
