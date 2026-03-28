"""
SuperMap iServer 服务发布工具

提供地图服务、数据服务、分析服务、三维服务的发布功能。
"""

import requests
import json
from typing import Dict, List, Optional
from pathlib import Path


class ServicePublisher:
    """iServer 服务发布器"""

    def __init__(self, server_url: str, token: Optional[str] = None, timeout: int = 60):
        """
        初始化服务发布器

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

    # ========== 地图服务 ==========

    def publish_map_service(
        self,
        workspace_path: str,
        map_name: str,
        service_name: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        发布地图服务

        Args:
            workspace_path: 工作空间文件路径
            map_name: 地图名称
            service_name: 服务名称
            config: 额外配置 (可选)

        Returns:
            发布结果
        """
        data = {
            "serviceInfos": [{
                "serviceName": service_name,
                "type": "map",
                "interfaceNames": ["rest", "wms", "wmts"],
                "mapName": map_name,
                "workspaces": [{
                    "name": map_name,
                    "type": "SMWU",
                    "connectionInfo": {
                        "server": workspace_path,
                        "engineType": "UDBX"
                    }
                }]
            }]
        }

        if config:
            data["serviceInfos"][0].update(config)

        response = self._post('/iserver/services', json_data=data)
        return response.json()

    # ========== 数据服务 ==========

    def publish_data_service(
        self,
        datasource_path: str,
        service_name: str,
        dataset_names: Optional[List[str]] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        发布数据服务

        Args:
            datasource_path: 数据源文件路径
            service_name: 服务名称
            dataset_names: 要发布的数据集列表 (None=全部)
            config: 额外配置 (可选)

        Returns:
            发布结果
        """
        data = {
            "serviceInfos": [{
                "serviceName": service_name,
                "type": "data",
                "interfaceNames": ["rest", "wfs"],
                "workspaces": [{
                    "name": service_name,
                    "type": "UDBX",
                    "connectionInfo": {
                        "server": datasource_path,
                        "engineType": "UDBX"
                    },
                    "dataInfos": [] if dataset_names is None else [
                        {"name": ds, "type": "UDBX"}
                        for ds in dataset_names
                    ]
                }]
            }]
        }

        if config:
            data["serviceInfos"][0].update(config)

        response = self._post('/iserver/services', json_data=data)
        return response.json()

    # ========== 分析服务 ==========

    def publish_analysis_service(
        self,
        workspace_path: str,
        service_name: str,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        发布空间分析服务

        Args:
            workspace_path: 工作空间文件路径
            service_name: 服务名称
            config: 额外配置 (可选)

        Returns:
            发布结果
        """
        data = {
            "serviceInfos": [{
                "serviceName": service_name,
                "type": "spatialanalyst",
                "interfaceNames": ["rest"],
                "workspaces": [{
                    "name": service_name,
                    "type": "SMWU",
                    "connectionInfo": {
                        "server": workspace_path,
                        "engineType": "UDBX"
                    }
                }]
            }]
        }

        if config:
            data["serviceInfos"][0].update(config)

        response = self._post('/iserver/services', json_data=data)
        return response.json()

    # ========== 三维服务 ==========

    def publish_3d_service(
        self,
        scene_name: str,
        service_name: str,
        workspace_path: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        发布三维服务

        Args:
            scene_name: 场景名称
            service_name: 服务名称
            workspace_path: 工作空间文件路径 (可选)
            config: 额外配置 (可选)

        Returns:
            发布结果
        """
        data = {
            "serviceInfos": [{
                "serviceName": service_name,
                "type": "3D",
                "interfaceNames": ["rest"],
                "sceneName": scene_name
            }]
        }

        if workspace_path:
            data["serviceInfos"][0]["workspaces"] = [{
                "name": service_name,
                "type": "SMWU",
                "connectionInfo": {
                    "server": workspace_path,
                    "engineType": "UDBX"
                }
            }]

        if config:
            data["serviceInfos"][0].update(config)

        response = self._post('/iserver/services', json_data=data)
        return response.json()

    # ========== 批量发布 ==========

    def batch_publish(
        self,
        service_type: str,
        services: List[Dict],
        overwrite: bool = False
    ) -> Dict[str, bool]:
        """
        批量发布服务

        Args:
            service_type: 服务类型 (map, data, analysis, 3d)
            services: 服务配置列表
            overwrite: 是否覆盖已存在服务

        Returns:
            发布结果字典 {service_name: success}
        """
        results = {}

        for service_config in services:
            service_name = service_config['name']
            print(f"正在发布: {service_name}")

            try:
                if service_type == "map":
                    result = self.publish_map_service(
                        workspace_path=service_config['workspace_path'],
                        map_name=service_config['map_name'],
                        service_name=service_name
                    )
                elif service_type == "data":
                    result = self.publish_data_service(
                        datasource_path=service_config['datasource_path'],
                        service_name=service_name,
                        dataset_names=service_config.get('dataset_names')
                    )
                elif service_type == "analysis":
                    result = self.publish_analysis_service(
                        workspace_path=service_config['workspace_path'],
                        service_name=service_name
                    )
                elif service_type == "3d":
                    result = self.publish_3d_service(
                        scene_name=service_config['scene_name'],
                        service_name=service_name
                    )
                else:
                    results[service_name] = False
                    continue

                results[service_name] = True
                print(f"✓ {service_name}: 发布成功")

            except Exception as e:
                results[service_name] = False
                print(f"✗ {service_name}: 发布失败 - {e}")

        return results


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例 1: 初始化发布器
    publisher = ServicePublisher(
        server_url="http://localhost:8090",
        token="your_token_here"
    )

    # 示例 2: 发布地图服务
    result = publisher.publish_map_service(
        workspace_path="D:/data/world.smwu",
        map_name="World",
        service_name="map-world"
    )
    print(f"发布结果: {result}")

    # 示例 3: 发布数据服务
    result = publisher.publish_data_service(
        datasource_path="D:/data/world.udbx",
        service_name="data-world",
        dataset_names=["Capitals", "Countries"]
    )
    print(f"发布结果: {result}")

    # 示例 4: 批量发布
    services = [
        {
            "name": "map-china",
            "workspace_path": "D:/data/china.smwu",
            "map_name": "China"
        },
        {
            "name": "map-usa",
            "workspace_path": "D:/data/usa.smwu",
            "map_name": "USA"
        }
    ]

    results = publisher.batch_publish(service_type="map", services=services)
    print(f"批量发布结果: {results}")
