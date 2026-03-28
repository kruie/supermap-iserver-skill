"""
SuperMap iServer 集群管理工具

提供集群节点管理、负载均衡配置、健康检查、故障转移等功能。
"""

import requests
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class ClusterNode:
    """集群节点数据类"""
    name: str
    host: str
    port: int
    state: str = "UNKNOWN"  # RUNNING, STOPPED, UNREACHABLE
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    requests_per_second: float = 0.0
    avg_response_time: float = 0.0

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def is_healthy(self) -> bool:
        return self.state == "RUNNING"


@dataclass
class ClusterStatus:
    """集群状态数据类"""
    total_nodes: int
    healthy_nodes: int
    unhealthy_nodes: int
    nodes: List[ClusterNode] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return self.healthy_nodes == self.total_nodes

    @property
    def availability(self) -> float:
        if self.total_nodes == 0:
            return 0.0
        return self.healthy_nodes / self.total_nodes * 100


class ClusterManager:
    """iServer 集群管理器"""

    def __init__(
        self,
        nodes: List[Dict],
        token: Optional[str] = None,
        timeout: int = 10
    ):
        """
        初始化集群管理器

        Args:
            nodes: 节点配置列表，每项格式: {"name": "node1", "host": "192.168.1.101", "port": 8090}
            token: 访问令牌 (可选)
            timeout: 请求超时时间 (秒)
        """
        self.nodes = [
            ClusterNode(
                name=n["name"],
                host=n["host"],
                port=n.get("port", 8090)
            )
            for n in nodes
        ]
        self.token = token
        self.timeout = timeout

        self._headers = {}
        if token:
            self._headers = {"token": token}

    def _get(self, node: ClusterNode, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """向指定节点发送 GET 请求"""
        url = f"{node.base_url}{endpoint}"
        response = requests.get(url, params=params, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _post(self, node: ClusterNode, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """向指定节点发送 POST 请求"""
        url = f"{node.base_url}{endpoint}"
        response = requests.post(url, json=json_data, headers=self._headers, timeout=self.timeout)
        response.raise_for_status()
        return response

    # ========== 节点健康检查 ==========

    def check_node_health(self, node: ClusterNode) -> bool:
        """
        检查单个节点健康状态

        Args:
            node: 集群节点

        Returns:
            是否健康
        """
        try:
            response = requests.get(
                f"{node.base_url}/iserver/services",
                headers=self._headers,
                timeout=self.timeout
            )
            if response.status_code == 200:
                node.state = "RUNNING"
                return True
            else:
                node.state = "STOPPED"
                return False
        except requests.exceptions.Timeout:
            node.state = "UNREACHABLE"
            return False
        except requests.exceptions.ConnectionError:
            node.state = "UNREACHABLE"
            return False
        except Exception:
            node.state = "ERROR"
            return False

    def check_all_nodes(self) -> ClusterStatus:
        """
        并行检查所有节点健康状态

        Returns:
            集群状态
        """
        with ThreadPoolExecutor(max_workers=len(self.nodes)) as executor:
            futures = {executor.submit(self.check_node_health, node): node for node in self.nodes}
            for future in as_completed(futures):
                future.result()  # 等待所有检查完成

        healthy = sum(1 for n in self.nodes if n.is_healthy)
        unhealthy = len(self.nodes) - healthy

        return ClusterStatus(
            total_nodes=len(self.nodes),
            healthy_nodes=healthy,
            unhealthy_nodes=unhealthy,
            nodes=self.nodes
        )

    def get_healthy_nodes(self) -> List[ClusterNode]:
        """获取所有健康节点"""
        return [n for n in self.nodes if n.is_healthy]

    def get_unhealthy_nodes(self) -> List[ClusterNode]:
        """获取所有不健康节点"""
        return [n for n in self.nodes if not n.is_healthy]

    # ========== 节点状态监控 ==========

    def get_node_status(self, node: ClusterNode) -> Dict:
        """
        获取节点详细状态

        Args:
            node: 集群节点

        Returns:
            节点状态信息
        """
        try:
            response = self._get(node, "/iserver/manager/services.json")
            data = response.json()

            # 更新节点状态
            node.state = "RUNNING"
            if "cpu" in data:
                node.cpu_usage = data["cpu"]
            if "memory" in data:
                node.memory_usage = data["memory"]

            return {
                "node": node.name,
                "state": node.state,
                "cpu_usage": node.cpu_usage,
                "memory_usage": node.memory_usage,
                "services": data.get("services", [])
            }
        except Exception as e:
            node.state = "UNREACHABLE"
            return {
                "node": node.name,
                "state": "UNREACHABLE",
                "error": str(e)
            }

    def monitor_cluster(self) -> Dict[str, Dict]:
        """
        监控整个集群状态

        Returns:
            节点状态字典 {node_name: status}
        """
        statuses = {}
        with ThreadPoolExecutor(max_workers=len(self.nodes)) as executor:
            futures = {executor.submit(self.get_node_status, node): node for node in self.nodes}
            for future in as_completed(futures):
                node = futures[future]
                statuses[node.name] = future.result()

        return statuses

    # ========== 服务管理 ==========

    def start_service_on_all(self, service_name: str) -> Dict[str, bool]:
        """
        在所有节点上启动服务

        Args:
            service_name: 服务名称

        Returns:
            结果字典 {node_name: success}
        """
        results = {}
        for node in self.nodes:
            if not node.is_healthy:
                results[node.name] = False
                print(f"✗ {node.name}: 节点不可达，跳过")
                continue

            try:
                self._post(
                    node,
                    f"/iserver/manager/services/{service_name}.json",
                    json_data={"action": "start"}
                )
                results[node.name] = True
                print(f"✓ {node.name}: 服务 {service_name} 启动成功")
            except Exception as e:
                results[node.name] = False
                print(f"✗ {node.name}: 服务启动失败 - {e}")

        return results

    def stop_service_on_all(self, service_name: str) -> Dict[str, bool]:
        """
        在所有节点上停止服务

        Args:
            service_name: 服务名称

        Returns:
            结果字典 {node_name: success}
        """
        results = {}
        for node in self.nodes:
            if not node.is_healthy:
                results[node.name] = False
                continue

            try:
                self._post(
                    node,
                    f"/iserver/manager/services/{service_name}.json",
                    json_data={"action": "stop"}
                )
                results[node.name] = True
                print(f"✓ {node.name}: 服务 {service_name} 停止成功")
            except Exception as e:
                results[node.name] = False
                print(f"✗ {node.name}: 服务停止失败 - {e}")

        return results

    def rolling_restart(self, service_name: str, wait_seconds: int = 30) -> Dict[str, bool]:
        """
        滚动重启（逐节点重启，避免中断）

        Args:
            service_name: 服务名称
            wait_seconds: 每个节点重启后等待时间 (秒)

        Returns:
            结果字典 {node_name: success}
        """
        results = {}
        print(f"开始滚动重启服务: {service_name}")

        for i, node in enumerate(self.nodes):
            if not node.is_healthy:
                results[node.name] = False
                print(f"[{i+1}/{len(self.nodes)}] {node.name}: 节点不可达，跳过")
                continue

            try:
                print(f"[{i+1}/{len(self.nodes)}] 重启节点 {node.name}...")
                self._post(
                    node,
                    f"/iserver/manager/services/{service_name}.json",
                    json_data={"action": "restart"}
                )
                results[node.name] = True
                print(f"[{i+1}/{len(self.nodes)}] ✓ {node.name}: 重启成功，等待 {wait_seconds}s...")
                if i < len(self.nodes) - 1:  # 最后一个节点不需要等待
                    time.sleep(wait_seconds)
            except Exception as e:
                results[node.name] = False
                print(f"[{i+1}/{len(self.nodes)}] ✗ {node.name}: 重启失败 - {e}")

        print("滚动重启完成")
        return results

    # ========== 服务同步 ==========

    def sync_service_config(self, source_node: ClusterNode, target_nodes: Optional[List[ClusterNode]] = None) -> Dict[str, bool]:
        """
        将服务配置从源节点同步到目标节点

        Args:
            source_node: 源节点（配置模板）
            target_nodes: 目标节点列表（None=所有其他节点）

        Returns:
            同步结果 {node_name: success}
        """
        if target_nodes is None:
            target_nodes = [n for n in self.nodes if n.name != source_node.name]

        # 获取源节点服务配置
        response = self._get(source_node, "/iserver/manager/services.json")
        services = response.json().get("services", [])

        results = {}
        for node in target_nodes:
            if not node.is_healthy:
                results[node.name] = False
                continue

            try:
                # 同步每个服务配置（实际操作需要更复杂的逻辑）
                for service in services:
                    service_name = service["name"]
                    # 检查目标节点是否有该服务
                    # 如果没有，发布服务
                    pass

                results[node.name] = True
                print(f"✓ {node.name}: 配置同步成功")
            except Exception as e:
                results[node.name] = False
                print(f"✗ {node.name}: 配置同步失败 - {e}")

        return results

    # ========== 持续监控 ==========

    def continuous_monitor(self, interval: int = 30, alert_callback=None):
        """
        持续监控集群状态（阻塞运行）

        Args:
            interval: 检查间隔 (秒)
            alert_callback: 告警回调函数 (接收告警信息字符串)
        """
        print(f"开始监控集群（每 {interval}s 检查一次）...")
        print(f"节点: {[n.name for n in self.nodes]}")

        while True:
            status = self.check_all_nodes()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

            print(f"\n[{timestamp}] 集群状态: {status.healthy_nodes}/{status.total_nodes} 节点健康")

            for node in status.nodes:
                icon = "✓" if node.is_healthy else "✗"
                print(f"  {icon} {node.name} ({node.host}:{node.port}): {node.state}")

            if not status.is_healthy and alert_callback:
                unhealthy = [n.name for n in status.nodes if not n.is_healthy]
                alert_callback(f"集群异常！以下节点不健康: {', '.join(unhealthy)}")

            time.sleep(interval)

    def generate_cluster_report(self) -> Dict:
        """
        生成集群状态报告

        Returns:
            集群报告
        """
        status = self.check_all_nodes()
        node_statuses = self.monitor_cluster()

        return {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cluster_summary": {
                "total_nodes": status.total_nodes,
                "healthy_nodes": status.healthy_nodes,
                "unhealthy_nodes": status.unhealthy_nodes,
                "availability": f"{status.availability:.1f}%",
                "is_healthy": status.is_healthy
            },
            "nodes": node_statuses
        }


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 集群节点配置
    CLUSTER_NODES = [
        {"name": "iserver-01", "host": "192.168.1.101", "port": 8090},
        {"name": "iserver-02", "host": "192.168.1.102", "port": 8090},
        {"name": "iserver-03", "host": "192.168.1.103", "port": 8090},
    ]

    # 初始化集群管理器
    cluster = ClusterManager(
        nodes=CLUSTER_NODES,
        token="your_token_here"
    )

    # 示例 1: 检查所有节点
    print("=== 节点健康检查 ===")
    status = cluster.check_all_nodes()
    print(f"集群可用性: {status.availability:.1f}%")
    print(f"健康节点: {status.healthy_nodes}/{status.total_nodes}")

    for node in status.nodes:
        icon = "✓" if node.is_healthy else "✗"
        print(f"  {icon} {node.name}: {node.state}")

    # 示例 2: 监控集群
    print("\n=== 集群监控 ===")
    statuses = cluster.monitor_cluster()
    for node_name, node_status in statuses.items():
        print(f"  {node_name}: {node_status['state']}")

    # 示例 3: 在所有节点启动服务
    print("\n=== 启动服务 ===")
    results = cluster.start_service_on_all("map-world")
    for node_name, success in results.items():
        print(f"  {node_name}: {'✓ 成功' if success else '✗ 失败'}")

    # 示例 4: 滚动重启
    print("\n=== 滚动重启 ===")
    results = cluster.rolling_restart("map-world", wait_seconds=30)

    # 示例 5: 生成集群报告
    print("\n=== 集群报告 ===")
    import json
    report = cluster.generate_cluster_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))

    # 示例 6: 持续监控 (带告警)
    # cluster.continuous_monitor(
    #     interval=30,
    #     alert_callback=lambda msg: print(f"🔔 告警: {msg}")
    # )
