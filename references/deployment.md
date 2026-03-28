# SuperMap iServer 部署指南

## 概述

本文档介绍 SuperMap iServer 的安装、配置、备份恢复等部署相关操作。

---

## 一、系统要求

### 1.1 硬件要求

| 规模 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 开发/测试 | 4 核 | 8 GB | 100 GB |
| 小型生产 | 8 核 | 16 GB | 500 GB |
| 中型生产 | 16 核 | 32 GB | 1 TB |
| 大型生产 | 32 核+ | 64 GB+ | 2 TB+ |

### 1.2 软件要求

**操作系统**:
- Windows Server 2016/2019/2022
- CentOS 7/8
- Ubuntu 18.04/20.04/22.04
- Red Hat Enterprise Linux 7/8

**Java 版本**:
- JDK 11 (推荐)
- JDK 8

**数据库** (可选):
- PostgreSQL 12+
- Oracle 19c+
- MySQL 8.0+

---

## 二、安装步骤

### 2.1 Windows 安装

```powershell
# 1. 下载安装包
# SuperMap_iServer_11i_2025_Setup.exe

# 2. 运行安装程序 (以管理员身份)
# 双击运行，按向导操作

# 3. 安装到默认目录
# C:\SuperMap\iServer11i

# 4. 启动 iServer 服务
# "开始菜单" -> "SuperMap iServer" -> "启动服务"
# 或通过 Windows 服务管理器

# 5. 验证安装
Start-Process "http://localhost:8090/iserver/manager"
```

**作为 Windows 服务安装**:

```powershell
# 注册服务
cd "C:\SuperMap\iServer11i\support"
.\iServerService.bat install

# 启动服务
net start SuperMapiServer

# 停止服务
net stop SuperMapiServer
```

### 2.2 Linux 安装

```bash
# 1. 下载安装包
# SuperMap_iServer_11i_2025_Linux64.tar.gz

# 2. 解压
tar -zxvf SuperMap_iServer_11i_2025_Linux64.tar.gz
cd SuperMap_iServer_11i_2025_Linux64

# 3. 运行安装脚本
chmod +x install.sh
./install.sh

# 默认安装目录: ~/SuperMap/iServer11i

# 4. 配置环境变量
echo 'export ISERVER_HOME=~/SuperMap/iServer11i' >> ~/.bashrc
echo 'export PATH=$PATH:$ISERVER_HOME/bin' >> ~/.bashrc
source ~/.bashrc

# 5. 启动 iServer
cd $ISERVER_HOME
./bin/iserver.sh start

# 6. 验证安装
curl http://localhost:8090/iserver/services
```

**配置为系统服务 (systemd)**:

```ini
# /etc/systemd/system/iserver.service
[Unit]
Description=SuperMap iServer
After=network.target

[Service]
Type=forking
User=iserver
Group=iserver
WorkingDirectory=/opt/iserver
ExecStart=/opt/iserver/bin/iserver.sh start
ExecStop=/opt/iserver/bin/iserver.sh stop
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启用和启动服务
sudo systemctl daemon-reload
sudo systemctl enable iserver
sudo systemctl start iserver

# 查看状态
sudo systemctl status iserver
```

---

## 三、基础配置

### 3.1 修改端口

**配置文件**: `iserver/etc/iserver-system.xml`

```xml
<server>
  <port>8090</port>      <!-- HTTP 端口 -->
  <sslPort>8443</sslPort> <!-- HTTPS 端口 -->
</server>
```

### 3.2 配置 JVM 内存

**Windows**: 编辑 `iserver/bin/setenv.bat`

```bat
set JAVA_OPTS=-Xms4g -Xmx8g -XX:+UseG1GC -XX:MaxGCPauseMillis=200
```

**Linux**: 编辑 `iserver/bin/setenv.sh`

```bash
export JAVA_OPTS="-Xms4g -Xmx8g -XX:+UseG1GC -XX:MaxGCPauseMillis=200"
```

**JVM 参数说明**:

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| `-Xms` | 初始堆大小 | 物理内存的 25% |
| `-Xmx` | 最大堆大小 | 物理内存的 50% |
| `-XX:+UseG1GC` | 使用 G1 垃圾收集器 | 推荐 |
| `-XX:MaxGCPauseMillis` | GC 最大暂停时间 | 200ms |

### 3.3 配置数据目录

```xml
<!-- iserver/etc/iserver-system.xml -->
<server>
  <workspace>
    <outputPath>D:/iserver/workspaces</outputPath>
  </workspace>
  <data>
    <outputPath>D:/iserver/data</outputPath>
  </data>
  <cache>
    <outputPath>D:/iserver/cache</outputPath>
  </cache>
  <log>
    <outputPath>D:/iserver/logs</outputPath>
  </log>
</server>
```

---

## 四、License 配置

### 4.1 联机 License

```bash
# iServer 启动后，访问管理界面
http://localhost:8090/iserver/manager

# 菜单: 系统 -> License -> 激活
# 输入 License Key 进行激活
```

### 4.2 离线 License

```bash
# 1. 获取机器码
./bin/iserver.sh getmachinecode

# 2. 使用机器码向超图申请 License 文件

# 3. 将 License 文件放置到
cp license.slm $ISERVER_HOME/license/

# 4. 重启 iServer
./bin/iserver.sh restart
```

### 4.3 查看 License 信息

```bash
# 命令行
./bin/iserver.sh licenseinfo

# 或访问管理界面
http://localhost:8090/iserver/manager -> 系统 -> License
```

---

## 五、升级

### 5.1 升级前准备

```bash
# 1. 备份当前配置
cp -r $ISERVER_HOME/etc $ISERVER_HOME/etc.bak.$(date +%Y%m%d)
cp -r $ISERVER_HOME/webapps $ISERVER_HOME/webapps.bak.$(date +%Y%m%d)

# 2. 导出服务配置
# 访问管理界面 -> 服务 -> 导出服务配置

# 3. 记录当前版本
./bin/iserver.sh version

# 4. 停止 iServer
./bin/iserver.sh stop
```

### 5.2 执行升级

```bash
# 1. 解压新版本
tar -zxvf SuperMap_iServer_11i_2025_sp1_Linux64.tar.gz

# 2. 运行升级脚本
./upgrade.sh $ISERVER_HOME

# 3. 启动新版本
./bin/iserver.sh start

# 4. 验证升级
./bin/iserver.sh version
curl http://localhost:8090/iserver/services
```

### 5.3 回滚

```bash
# 如果升级失败，回滚到旧版本
./bin/iserver.sh stop

# 恢复备份
cp -r $ISERVER_HOME/etc.bak.20260327 $ISERVER_HOME/etc
cp -r $ISERVER_HOME/webapps.bak.20260327 $ISERVER_HOME/webapps

# 启动旧版本
./bin/iserver.sh start
```

---

## 六、备份与恢复

### 6.1 备份内容清单

| 类别 | 路径 | 重要性 |
|------|------|--------|
| 系统配置 | `iserver/etc/` | ⭐⭐⭐ 必须 |
| 服务配置 | `iserver/webapps/iserver/WEB-INF/` | ⭐⭐⭐ 必须 |
| License | `iserver/license/` | ⭐⭐⭐ 必须 |
| 工作空间 | 自定义路径 | ⭐⭐⭐ 必须 |
| 地图缓存 | 自定义路径 | ⭐⭐ 建议 |
| 日志 | `iserver/logs/` | ⭐ 可选 |

### 6.2 手动备份脚本

```bash
#!/bin/bash
# backup_iserver.sh

ISERVER_HOME="/opt/iserver"
BACKUP_DIR="/backup/iserver"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$DATE"

echo "=== 开始备份 iServer ==="

# 创建备份目录
mkdir -p $BACKUP_PATH

# 备份配置文件
echo "备份配置文件..."
cp -r $ISERVER_HOME/etc $BACKUP_PATH/etc
cp -r $ISERVER_HOME/license $BACKUP_PATH/license

# 备份工作空间
echo "备份工作空间..."
cp -r /data/iserver/workspaces $BACKUP_PATH/workspaces

# 压缩备份
echo "压缩备份..."
tar -czf $BACKUP_DIR/iserver_backup_$DATE.tar.gz -C $BACKUP_DIR $DATE
rm -rf $BACKUP_PATH

# 删除 30 天前的备份
find $BACKUP_DIR -name "iserver_backup_*.tar.gz" -mtime +30 -delete

echo "=== 备份完成: $BACKUP_DIR/iserver_backup_$DATE.tar.gz ==="
```

### 6.3 自动备份 (定时任务)

```bash
# 每天凌晨 2:00 自动备份
crontab -e
# 添加以下内容:
0 2 * * * /opt/scripts/backup_iserver.sh >> /var/log/iserver_backup.log 2>&1
```

### 6.4 恢复步骤

```bash
#!/bin/bash
# restore_iserver.sh

BACKUP_FILE="$1"  # 备份文件路径
ISERVER_HOME="/opt/iserver"
RESTORE_DIR="/tmp/iserver_restore"

if [ -z "$BACKUP_FILE" ]; then
    echo "用法: ./restore_iserver.sh /path/to/backup.tar.gz"
    exit 1
fi

echo "=== 开始恢复 iServer ==="

# 停止 iServer
echo "停止 iServer..."
$ISERVER_HOME/bin/iserver.sh stop

# 解压备份
echo "解压备份文件..."
mkdir -p $RESTORE_DIR
tar -xzf $BACKUP_FILE -C $RESTORE_DIR

# 获取备份目录名
BACKUP_SUBDIR=$(ls $RESTORE_DIR)

# 恢复配置文件
echo "恢复配置文件..."
cp -r $RESTORE_DIR/$BACKUP_SUBDIR/etc/* $ISERVER_HOME/etc/
cp -r $RESTORE_DIR/$BACKUP_SUBDIR/license/* $ISERVER_HOME/license/

# 恢复工作空间
echo "恢复工作空间..."
cp -r $RESTORE_DIR/$BACKUP_SUBDIR/workspaces/* /data/iserver/workspaces/

# 清理临时目录
rm -rf $RESTORE_DIR

# 启动 iServer
echo "启动 iServer..."
$ISERVER_HOME/bin/iserver.sh start

echo "=== 恢复完成 ==="
```

---

## 七、Docker 部署

### 7.1 Docker 安装

```dockerfile
# Dockerfile
FROM ubuntu:22.04

# 安装依赖
RUN apt-get update && apt-get install -y \
    openjdk-11-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置 JAVA_HOME
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

# 复制 iServer 安装包
COPY SuperMap_iServer_11i_2025_Linux64.tar.gz /tmp/
RUN cd /tmp && \
    tar -zxvf SuperMap_iServer_11i_2025_Linux64.tar.gz && \
    ./SuperMap_iServer_11i_2025_Linux64/install.sh -d /opt/iserver && \
    rm -rf /tmp/SuperMap_iServer_11i_2025_Linux64*

# 暴露端口
EXPOSE 8090 8443

# 设置工作目录
WORKDIR /opt/iserver

# 启动命令
CMD ["./bin/iserver.sh", "run"]
```

### 7.2 Docker Compose 部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  iserver:
    image: supermap/iserver:11i-2025
    container_name: iserver
    ports:
      - "8090:8090"
      - "8443:8443"
    volumes:
      - ./config:/opt/iserver/etc
      - ./workspaces:/data/workspaces
      - ./cache:/data/cache
      - ./logs:/opt/iserver/logs
    environment:
      - JAVA_OPTS=-Xms2g -Xmx4g
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8090/iserver/services"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
# 启动
docker-compose up -d

# 停止
docker-compose down

# 查看日志
docker-compose logs -f iserver
```

---

## 八、常见部署问题

### 问题 1: 端口被占用

```bash
# 查看端口占用
netstat -tlnp | grep 8090

# Windows
netstat -ano | findstr 8090

# 修改 iServer 端口
# 编辑 iserver/etc/iserver-system.xml
```

### 问题 2: 内存不足

```bash
# 查看当前内存
free -h

# 增加 JVM 堆内存
# 编辑 iserver/bin/setenv.sh
export JAVA_OPTS="-Xms2g -Xmx4g"
```

### 问题 3: 权限问题

```bash
# Linux 权限问题
chmod +x $ISERVER_HOME/bin/*.sh
chown -R iserver:iserver $ISERVER_HOME
```

### 问题 4: License 无效

```bash
# 检查 License 文件
ls -la $ISERVER_HOME/license/

# 重新激活
http://localhost:8090/iserver/manager -> 系统 -> License
```

---

**文档版本**: v1.0
**更新时间**: 2026-03-28
**适用版本**: SuperMap iServer 11i (2025)
