"""
SuperMap iServer 服务管理工具

提供服务的启停、重启、状态查询、缓存管理等管理功能。
"""

import requests
from typing import Dict, List, Optional
from enum import Enum


class ServiceState(Enum):
    """服务状态枚举"""
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"


class ServiceManager:
    """iServer 服务管理器"""

    def __init__(self, server_url: str, token: Optional[str] = None, timeout: int = 30):
        """
        初始化服务管理器

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

    def _post(self, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """发送 POST 请求"""
        url = f"{self.server_url}{endpoint}"
        response = self.session.post(url, json=json_data, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送 GET 请求"""
        url = f"{self.server_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    # ========== 服务启停 ==========

    def start_service(self, service_name: str) -> Dict:
        """
        启动服务

        Args:
            service_name: 服务名称

        Returns:
            启动结果
        """
        response = self._post(f'/iserver/manager/services/{service_name}.json', json_data={'action': 'start'})
        return response.json()

    def stop_service(self, service_name: str) -> Dict:
        """
        停止服务

        Args:
            service_name: 服务名称

        Returns:
            停止结果
        """
        response = self._post(f'/iserver/manager/services/{service_name}.json', json_data={'action': 'stop'})
        return response.json()

    def restart_service(self, service_name: str) -> Dict:
        """
        重启服务

        Args:
            service_name: 服务名称

        Returns:
            重启结果
        """
        response = self._post(f'/iserver/manager/services/{service_name}.json', json_data={'action': 'restart'})
        return response.json()

    # ========== 服务状态 ==========

    def get_service_status(self, service_name: str) -> Dict:
        """
        获取服务状态

        Args:
            service_name: 服务名称

        Returns:
            服务状态信息
        """
        response = self._get(f'/iserver/manager/services/{service_name}.json')
        return response.json()

    def list_services(self) -> List[Dict]:
        """
        获取所有服务列表

        Returns:
            服务列表
        """
        response = self._get('/iserver/manager/services.json')
        return response.json()

    # ========== 缓存管理 ==========

    def clear_cache(self, service_name: str, cache_type: str = "all") -> Dict:
        """
        清除缓存

        Args:
            service_name: 服务名称
            cache_type: 缓存类型 (all, map, image)

        Returns:
            清除结果
        """
        response = self._post(
            f'/iserver/manager/clearcache/{service_name}.json',
            json_data={'cacheType': cache_type}
        )
        return response.json()

    def pre_generate_cache(
        self,
        service_name: str,
        scale: float,
        bounds: Optional[tuple] = None
    ) -> Dict:
        """
        预生成缓存

        Args:
            service_name: 服务名称
            scale: 比例尺
            bounds: 范围 (minX, minY, maxX, maxY)

        Returns:
            生成结果
        """
        data = {'scale': scale}
        if bounds:
            data['bounds'] = f'{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}'

        response = self._post(f'/iserver/manager/precache/{service_name}.json', json_data=data)
        return response.json()

    # ========== 批量操作 ==========

    def start_all_services(self) -> Dict[str, Dict]:
        """启动所有服务"""
        services = self.list_services()
        results = {}

        for service in services:
            service_name = service['name']
            try:
                result = self.start_service(service_name)
                results[service_name] = result
                print(f"✓ {service_name}: 启动成功")
            except Exception as e:
                results[service_name] = {'error': str(e)}
                print(f"✗ {service_name}: 启动失败 - {e}")

        return results

    def stop_all_services(self) -> Dict[str, Dict]:
        """停止所有服务"""
        services = self.list_services()
        results = {}

        for service in services:
            service_name = service['name']
            try:
                result = self.stop_service(service_name)
                results[service_name] = result
                print(f"✓ {service_name}: 停止成功")
            except Exception as e:
                results[service_name] = {'error': str(e)}
                print(f"✗ {service_name}: 停止失败 - {e}")

        return results


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例 1: 初始化服务管理器
    manager = ServiceManager(
        server_url="http://localhost:8090",
        token="your_token_here"
    )

    # 示例 2: 获取服务列表
    services = manager.list_services()
    print("服务列表:")
    for service in services:
        print(f"  - {service['name']}")

    # 示例 3: 启动服务
    result = manager.start_service("map-world")
    print(f"启动结果: {result}")

    # 示例 4: 停止服务
    result = manager.stop_service("map-world")
    print(f"停止结果: {result}")

    # 示例 5: 获取服务状态
    status = manager.get_service_status("map-world")
    print(f"服务状态: {status}")

    # 示例 6: 清除缓存
    result = manager.clear_cache("map-world", cache_type="all")
    print(f"清除缓存: {result}")
