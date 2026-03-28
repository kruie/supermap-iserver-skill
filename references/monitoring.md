# SuperMap iServer 监控与日志指南

## 概述

本文档介绍如何对 SuperMap iServer 进行全面监控，包括服务状态、性能指标、日志分析和告警配置。

---

## 一、内置监控

### 1.1 iServer 管理界面监控

访问 `http://localhost:8090/iserver/manager` 可以查看：

- **服务状态**: 所有服务的运行状态（RUNNING / STOPPED）
- **访问统计**: 各服务的请求量、响应时间
- **系统信息**: CPU、内存、线程数等

### 1.2 REST API 监控接口

```bash
# 获取服务状态
GET /iserver/manager/services.json

# 获取单个服务状态
GET /iserver/manager/services/{service_name}.json

# 获取性能统计
GET /iserver/manager/stats.json

# 获取系统信息
GET /iserver/manager/system.json
```

---

## 二、日志配置

### 2.1 日志文件位置

| 日志类型 | 路径 | 内容 |
|---------|------|------|
| 主日志 | `logs/iserver.log` | 启动/停止、服务发布等 |
| 访问日志 | `logs/access.log` | 所有 HTTP 请求 |
| 错误日志 | `logs/error.log` | 错误和异常信息 |
| GC 日志 | `logs/gc.log` | Java GC 信息 |

### 2.2 日志级别配置

**配置文件**: `iserver/etc/log4j2.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Configuration status="WARN">
  <Appenders>
    <!-- 控制台输出 -->
    <Console name="Console" target="SYSTEM_OUT">
      <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss} [%t] %-5level %logger{36} - %msg%n"/>
    </Console>

    <!-- 文件输出 -->
    <RollingFile name="File"
                 fileName="logs/iserver.log"
                 filePattern="logs/iserver-%d{yyyy-MM-dd}-%i.log.gz">
      <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss} [%t] %-5level %logger{36} - %msg%n"/>
      <Policies>
        <TimeBasedTriggeringPolicy />
        <SizeBasedTriggeringPolicy size="100 MB"/>
      </Policies>
      <DefaultRolloverStrategy max="30"/>
    </RollingFile>

    <!-- 错误日志 -->
    <RollingFile name="ErrorFile"
                 fileName="logs/error.log"
                 filePattern="logs/error-%d{yyyy-MM-dd}.log.gz">
      <ThresholdFilter level="ERROR" onMatch="ACCEPT" onMismatch="DENY"/>
      <PatternLayout pattern="%d{yyyy-MM-dd HH:mm:ss} [%t] %-5level %logger{36} - %msg%n"/>
      <Policies>
        <TimeBasedTriggeringPolicy />
      </Policies>
    </RollingFile>
  </Appenders>

  <Loggers>
    <!-- 根日志级别 -->
    <Root level="INFO">
      <AppenderRef ref="Console"/>
      <AppenderRef ref="File"/>
      <AppenderRef ref="ErrorFile"/>
    </Root>

    <!-- 特定包日志级别 -->
    <Logger name="com.supermap.server" level="DEBUG" additivity="false">
      <AppenderRef ref="File"/>
    </Logger>
  </Loggers>
</Configuration>
```

### 2.3 访问日志格式

```xml
<!-- 配置访问日志 -->
<accessLog>
  <enabled>true</enabled>
  <format>%h %l %u %t "%r" %s %b %D</format>
  <!-- 字段说明:
    %h: 远程主机 IP
    %l: 远程登录名
    %u: 认证用户名
    %t: 请求时间
    %r: 请求行 (方法 URL 协议)
    %s: 响应状态码
    %b: 响应字节数
    %D: 处理时间 (毫秒)
  -->
</accessLog>
```

---

## 三、监控指标

### 3.1 核心监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|---------|
| 服务状态 | RUNNING / STOPPED | 任意服务 STOPPED |
| CPU 使用率 | 总体 CPU 占用 | > 80% |
| 内存使用率 | JVM 堆内存占用 | > 85% |
| 请求响应时间 | 平均 / P95 / P99 | P95 > 2s |
| 错误率 | 失败请求 / 总请求 | > 1% |
| 连接数 | 活跃 HTTP 连接数 | > 最大连接数的 80% |
| 线程数 | 活跃线程数 | > 最大线程数的 80% |

### 3.2 使用 scripts/service_monitor.py 监控

```python
from scripts.service_monitor import ServiceMonitor

monitor = ServiceMonitor("http://localhost:8090", token="xxx")

# 实时监控所有服务
statuses = monitor.monitor_all_services()
for name, status in statuses.items():
    print(f"{name}: {status.state} | CPU: {status.cpu_usage:.1f}% | 内存: {status.memory_usage:.0f}MB")

# 生成日报
report = monitor.generate_performance_report(hours=24)
monitor.save_report(report, "daily_report.html")
```

---

## 四、Prometheus + Grafana 监控

### 4.1 配置 Prometheus 抓取 iServer 指标

iServer 支持 Prometheus 格式的指标输出：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'iserver'
    static_configs:
      - targets: ['localhost:8090']
    metrics_path: '/iserver/metrics'
    params:
      format: ['prometheus']
    bearer_token: 'your_token'
    scrape_interval: 15s
```

### 4.2 常用 Grafana 面板查询

```promql
# 服务请求率 (每秒)
rate(iserver_requests_total[5m])

# 平均响应时间
iserver_response_time_avg_ms

# CPU 使用率
iserver_cpu_usage_percent

# 堆内存使用
iserver_heap_used_bytes / iserver_heap_max_bytes * 100

# 活跃连接数
iserver_active_connections

# 错误率
rate(iserver_requests_failed_total[5m]) / rate(iserver_requests_total[5m]) * 100
```

---

## 五、告警配置

### 5.1 使用 Python 脚本告警

```python
#!/usr/bin/env python3
"""
iServer 告警脚本 - 定时检查服务状态并发送告警
"""
import time
import smtplib
from email.mime.text import MIMEText
from scripts.service_monitor import ServiceMonitor


MONITOR = ServiceMonitor("http://localhost:8090", token="xxx")

# 告警阈值
THRESHOLDS = {
    "cpu_usage": 80.0,        # CPU 使用率超过 80% 告警
    "memory_usage": 8192,     # 内存使用超过 8GB 告警
    "avg_response_time": 2000 # 平均响应时间超过 2s 告警
}

# 邮件配置
EMAIL_CONFIG = {
    "smtp_host": "smtp.example.com",
    "smtp_port": 465,
    "sender": "iserver-alert@example.com",
    "password": "email_password",
    "recipients": ["admin@example.com"]
}


def send_alert(subject: str, body: str):
    """发送告警邮件"""
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = f"[iServer 告警] {subject}"
    msg["From"] = EMAIL_CONFIG["sender"]
    msg["To"] = ", ".join(EMAIL_CONFIG["recipients"])

    with smtplib.SMTP_SSL(EMAIL_CONFIG["smtp_host"], EMAIL_CONFIG["smtp_port"]) as smtp:
        smtp.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
        smtp.sendmail(EMAIL_CONFIG["sender"], EMAIL_CONFIG["recipients"], msg.as_string())

    print(f"告警已发送: {subject}")


def check_and_alert():
    """检查服务状态并发送告警"""
    statuses = MONITOR.monitor_all_services()

    alerts = []

    for service_name, status in statuses.items():
        # 服务停止告警
        if status.state != "RUNNING":
            alerts.append(f"❌ 服务 {service_name} 已停止 (状态: {status.state})")

        # CPU 告警
        if status.cpu_usage > THRESHOLDS["cpu_usage"]:
            alerts.append(f"⚠️ 服务 {service_name} CPU 使用率过高: {status.cpu_usage:.1f}%")

        # 内存告警
        if status.memory_usage > THRESHOLDS["memory_usage"]:
            alerts.append(f"⚠️ 服务 {service_name} 内存使用过高: {status.memory_usage:.0f}MB")

        # 响应时间告警
        if status.avg_response_time > THRESHOLDS["avg_response_time"]:
            alerts.append(f"⚠️ 服务 {service_name} 响应时间过慢: {status.avg_response_time:.0f}ms")

    if alerts:
        body = "\n".join(alerts)
        body += f"\n\n检查时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        body += f"\n服务器: http://localhost:8090/iserver/manager"
        send_alert("服务异常告警", body)

    return alerts


if __name__ == "__main__":
    # 每 5 分钟检查一次
    while True:
        alerts = check_and_alert()
        if alerts:
            print(f"发现 {len(alerts)} 个告警")
        else:
            print("所有服务正常")
        time.sleep(300)
```

### 5.2 配置 Alertmanager (配合 Prometheus)

```yaml
# alertmanager.yml
global:
  smtp_smarthost: 'smtp.example.com:465'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager@example.com'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 1h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'admin@example.com'
        subject: '[iServer 告警] {{ .CommonAnnotations.summary }}'
        body: '{{ .CommonAnnotations.description }}'
```

```yaml
# alert_rules.yml (Prometheus 告警规则)
groups:
  - name: iserver_alerts
    rules:
      - alert: iServerServiceDown
        expr: iserver_service_state{state="STOPPED"} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "iServer 服务停止"
          description: "服务 {{ $labels.service_name }} 已停止运行"

      - alert: iServerHighCPU
        expr: iserver_cpu_usage_percent > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "iServer CPU 使用率过高"
          description: "服务 {{ $labels.service_name }} CPU 使用率: {{ $value }}%"

      - alert: iServerHighMemory
        expr: iserver_heap_used_bytes / iserver_heap_max_bytes > 0.85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "iServer 内存使用过高"
          description: "JVM 堆内存使用率: {{ $value | humanizePercentage }}"

      - alert: iServerSlowResponse
        expr: iserver_response_time_p95_ms > 2000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "iServer 响应时间过慢"
          description: "P95 响应时间: {{ $value }}ms"
```

---

## 六、日志分析

### 6.1 常见日志模式分析

```bash
# 统计每小时请求量
grep "2026-03-28" logs/access.log | awk '{print $4}' | cut -d: -f2 | sort | uniq -c

# 统计 HTTP 状态码分布
awk '{print $9}' logs/access.log | sort | uniq -c | sort -rn

# 查找慢请求 (响应时间 > 5000ms)
awk '$NF > 5000' logs/access.log

# 统计 Top 10 访问 URL
awk '{print $7}' logs/access.log | sort | uniq -c | sort -rn | head -10

# 查找错误日志
grep "ERROR" logs/iserver.log | tail -100

# 统计错误类型
grep "ERROR" logs/iserver.log | awk '{print $5}' | sort | uniq -c | sort -rn
```

### 6.2 使用 ELK Stack 集中日志

```yaml
# filebeat.yml - 收集 iServer 日志
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /opt/iserver/logs/*.log
    fields:
      service: iserver
    fields_under_root: true
    multiline.pattern: '^\d{4}-\d{2}-\d{2}'
    multiline.negate: true
    multiline.match: after

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
  index: "iserver-logs-%{+yyyy.MM.dd}"
```

---

## 七、监控大盘示例

### 7.1 Grafana 大盘布局

```
+-------------------+-------------------+-------------------+
|  服务状态总览      |  请求量/分钟        |  平均响应时间       |
|  ● 运行: 5/5      |  📊 1,200 req/min  |  ⏱️ 245ms          |
+-------------------+-------------------+-------------------+
|  CPU 使用率趋势 (24h)                                       |
|  ████████████░░░░  35%                                     |
+-----------------------------------------------------------+
|  内存使用趋势 (24h)                                         |
|  ██████████████░░  70%                                     |
+-----------------------------------------------------------+
|  各服务请求量排行              |  错误日志实时流              |
|  map-world: 800               |  [ERROR] ...               |
|  data-cities: 300             |  [WARN] ...                |
|  spatialanalyst: 100          |                             |
+-------------------+-----------+----------------------------+
```

---

## 八、故障排查流程

### 8.1 服务无响应

```
1. 检查服务状态
   → GET /iserver/manager/services/{name}.json
   
2. 检查系统资源
   → top / htop (Linux)
   → 任务管理器 (Windows)
   
3. 检查 iServer 日志
   → tail -f logs/iserver.log
   → grep ERROR logs/error.log
   
4. 检查 JVM 状态
   → jstack <pid> (线程栈)
   → jmap -heap <pid> (堆内存)
   
5. 重启服务 (最后手段)
   → ./bin/iserver.sh restart
```

### 8.2 响应缓慢

```
1. 检查响应时间分布
   → awk '$NF > 2000' logs/access.log | tail -50
   
2. 检查慢请求 URL
   → awk '$NF > 2000 {print $7}' logs/access.log | sort | uniq -c | sort -rn
   
3. 检查是否命中缓存
   → 查看 Cache-Control 响应头
   
4. 检查数据量
   → 大数据集查询可能超时
   
5. 检查 CPU/内存
   → 系统资源是否充足
   
6. 优化措施
   → 启用缓存
   → 增加 JVM 内存
   → 优化查询
```

---

**文档版本**: v1.0  
**更新时间**: 2026-03-28  
**适用版本**: SuperMap iServer 11i (2025)
