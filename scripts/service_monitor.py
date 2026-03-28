"""
SuperMap iServer 服务监控工具

提供服务性能监控、访问统计、错误日志收集等功能。
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class ServiceStatus:
    """服务状态数据类"""
    state: str  # RUNNING, STOPPED, ERROR
    cpu_usage: float  # CPU 使用率 (%)
    memory_usage: float  # 内存使用 (MB)
    requests_per_second: float  # 请求/秒
    avg_response_time: float  # 平均响应时间 (ms)
    uptime: float  # 运行时间 (秒)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""
    timestamp: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    max_response_time: float
    min_response_time: float


class ServiceMonitor:
    """iServer 服务监控器"""

    def __init__(
        self,
        server_url: str,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化监控器

        Args:
            server_url: iServer 服务器地址
            token: 访问令牌 (可选)
            timeout: 请求超时时间 (秒)
        """
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.session = requests.Session()

        if token:
            self.session.headers.update({'token': token})

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送 GET 请求"""
        url = f"{self.server_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    # ========== 服务状态监控 ==========

    def get_service_status(self, service_name: str) -> ServiceStatus:
        """
        获取服务状态

        Args:
            service_name: 服务名称

        Returns:
            服务状态对象
        """
        response = self._get(f'/iserver/manager/services/{service_name}.json')
        data = response.json()

        return ServiceStatus(
            state=data.get('state', 'UNKNOWN'),
            cpu_usage=data.get('cpuUsage', 0.0),
            memory_usage=data.get('memoryUsage', 0.0),
            requests_per_second=data.get('requestsPerSecond', 0.0),
            avg_response_time=data.get('avgResponseTime', 0.0),
            uptime=data.get('uptime', 0.0)
        )

    def monitor_all_services(self) -> Dict[str, ServiceStatus]:
        """
        监控所有服务状态

        Returns:
            服务状态字典 {service_name: ServiceStatus}
        """
        response = self._get('/iserver/manager/services.json')
        services = response.json()

        statuses = {}
        for service in services:
            service_name = service['name']
            try:
                status = self.get_service_status(service_name)
                statuses[service_name] = status
            except Exception as e:
                print(f"获取服务 {service_name} 状态失败: {e}")
                statuses[service_name] = ServiceStatus(
                    state='ERROR',
                    cpu_usage=0.0,
                    memory_usage=0.0,
                    requests_per_second=0.0,
                    avg_response_time=0.0,
                    uptime=0.0
                )

        return statuses

    # ========== 性能监控 ==========

    def monitor_performance(
        self,
        duration: int = 60,
        interval: int = 5
    ) -> Dict[str, List[PerformanceMetrics]]:
        """
        持续监控性能

        Args:
            duration: 监控时长 (秒)
            interval: 采样间隔 (秒)

        Returns:
            性能指标字典 {service_name: List[PerformanceMetrics]}
        """
        end_time = time.time() + duration
        metrics = {}

        while time.time() < end_time:
            timestamp = datetime.now()
            statuses = self.monitor_all_services()

            for service_name, status in statuses.items():
                if service_name not in metrics:
                    metrics[service_name] = []

                # 模拟性能指标 (实际应从 iServer 获取)
                perf = PerformanceMetrics(
                    timestamp=timestamp,
                    total_requests=int(status.requests_per_second * interval),
                    successful_requests=int(status.requests_per_second * interval * 0.95),
                    failed_requests=int(status.requests_per_second * interval * 0.05),
                    avg_response_time=status.avg_response_time,
                    max_response_time=status.avg_response_time * 1.5,
                    min_response_time=status.avg_response_time * 0.5
                )
                metrics[service_name].append(perf)

            time.sleep(interval)

        return metrics

    # ========== 访问统计 ==========

    def get_access_stats(
        self,
        service_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict:
        """
        获取访问统计

        Args:
            service_name: 服务名称
            start_time: 开始时间 (默认 24 小时前)
            end_time: 结束时间 (默认当前)

        Returns:
            访问统计数据
        """
        if not start_time:
            start_time = datetime.now() - timedelta(hours=24)
        if not end_time:
            end_time = datetime.now()

        params = {
            'serviceName': service_name,
            'startTime': start_time.isoformat(),
            'endTime': end_time.isoformat()
        }

        response = self._get('/iserver/manager/accessstats.json', params=params)
        return response.json()

    # ========== 错误日志 ==========

    def get_error_logs(
        self,
        service_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        获取错误日志

        Args:
            service_name: 服务名称 (None=所有服务)
            limit: 返回数量限制

        Returns:
            错误日志列表
        """
        params = {'limit': limit}
        if service_name:
            params['serviceName'] = service_name

        response = self._get('/iserver/manager/errorlogs.json', params=params)
        return response.json().get('logs', [])

    # ========== 性能报告 ==========

    def generate_performance_report(
        self,
        hours: int = 24
    ) -> Dict:
        """
        生成性能报告

        Args:
            hours: 统计时长 (小时)

        Returns:
            性能报告
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'time_range': f"{hours} 小时",
            'services': {}
        }

        statuses = self.monitor_all_services()

        for service_name, status in statuses.items():
            stats = self.get_access_stats(service_name)
            logs = self.get_error_logs(service_name, limit=50)

            report['services'][service_name] = {
                'state': status.state,
                'cpu_usage': status.cpu_usage,
                'memory_usage': status.memory_usage,
                'requests_per_second': status.requests_per_second,
                'avg_response_time': status.avg_response_time,
                'uptime_seconds': status.uptime,
                'total_requests': stats.get('totalRequests', 0),
                'successful_requests': stats.get('successfulRequests', 0),
                'failed_requests': stats.get('failedRequests', 0),
                'error_count': len(logs),
                'recent_errors': logs[:5]
            }

        return report

    def save_report(
        self,
        report: Dict,
        output_path: str,
        format: str = "html"
    ):
        """
        保存性能报告

        Args:
            report: 性能报告
            output_path: 输出路径
            format: 输出格式 (html, json)
        """
        if format == "html":
            html_content = self._report_to_html(report)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
        elif format == "json":
            import json
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")

    def _report_to_html(self, report: Dict) -> str:
        """将报告转换为 HTML"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>iServer 性能报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .running {{ color: green; font-weight: bold; }}
        .stopped {{ color: red; font-weight: bold; }}
        .error {{ color: red; }}
    </style>
</head>
<body>
    <h1>iServer 性能报告</h1>
    <p>生成时间: {report['generated_at']}</p>
    <p>统计范围: {report['time_range']}</p>
"""

        for service_name, data in report['services'].items():
            state_class = 'running' if data['state'] == 'RUNNING' else 'stopped'
            html += f"""
    <h2>服务: {service_name}</h2>
    <table>
        <tr><th>状态</th><td class="{state_class}">{data['state']}</td></tr>
        <tr><th>CPU 使用率</th><td>{data['cpu_usage']:.2f}%</td></tr>
        <tr><th>内存使用</th><td>{data['memory_usage']:.2f} MB</td></tr>
        <tr><th>请求/秒</th><td>{data['requests_per_second']:.2f}</td></tr>
        <tr><th>平均响应时间</th><td>{data['avg_response_time']:.2f} ms</td></tr>
        <tr><th>运行时间</th><td>{data['uptime_seconds']:.0f} 秒</td></tr>
        <tr><th>总请求数</th><td>{data['total_requests']}</td></tr>
        <tr><th>成功请求数</th><td>{data['successful_requests']}</td></tr>
        <tr><th>失败请求数</th><td class="error">{data['failed_requests']}</td></tr>
        <tr><th>错误数量</th><td>{data['error_count']}</td></tr>
    </table>
"""

        html += """
</body>
</html>
"""
        return html


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例 1: 初始化监控器
    monitor = ServiceMonitor(
        server_url="http://localhost:8090",
        token="your_token_here"
    )

    # 示例 2: 监控所有服务
    statuses = monitor.monitor_all_services()
    print("服务状态:")
    for service_name, status in statuses.items():
        print(f"  {service_name}:")
        print(f"    状态: {status.state}")
        print(f"    CPU: {status.cpu_usage:.2f}%")
        print(f"    内存: {status.memory_usage:.2f} MB")

    # 示例 3: 获取访问统计
    stats = monitor.get_access_stats("map-world")
    print(f"访问统计: {stats}")

    # 示例 4: 获取错误日志
    logs = monitor.get_error_logs("map-world", limit=10)
    print(f"错误日志 ({len(logs)} 条):")
    for log in logs[:5]:
        print(f"  [{log['timestamp']}] {log['level']}: {log['message']}")

    # 示例 5: 生成性能报告
    report = monitor.generate_performance_report(hours=24)
    monitor.save_report(report, "performance_report.html", format="html")
    print("性能报告已保存至 performance_report.html")
