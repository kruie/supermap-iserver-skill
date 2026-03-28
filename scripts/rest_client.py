"""
SuperMap iServer REST API 客户端

提供便捷的 REST API 调用接口,支持地图服务、数据服务、分析服务等。
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin


class iServerClient:
    """SuperMap iServer REST API 客户端"""

    def __init__(
        self,
        server_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化 iServer 客户端

        Args:
            server_url: iServer 服务器地址,如 http://localhost:8090
            token: 访问令牌 (可选)
            username: 用户名 (可选,用于获取令牌)
            password: 密码 (可选)
            timeout: 请求超时时间 (秒)
        """
        self.server_url = server_url.rstrip('/')
        self.token = token
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()

        if token:
            self.session.headers.update({'token': token})

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送 GET 请求"""
        url = urljoin(self.server_url, endpoint)
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _post(self, endpoint: str, data: Optional[Dict] = None, json_data: Optional[Dict] = None) -> requests.Response:
        """发送 POST 请求"""
        url = urljoin(self.server_url, endpoint)
        response = self.session.post(url, data=data, json=json_data, timeout=self.timeout)
        response.raise_for_status()
        return response

    # ========== 服务管理 ==========

    def list_services(self) -> List[Dict]:
        """
        获取服务列表

        Returns:
            服务列表
        """
        response = self._get('/iserver/services')
        return response.json()

    def get_service_info(self, service_name: str) -> Dict:
        """
        获取服务详细信息

        Args:
            service_name: 服务名称

        Returns:
            服务信息
        """
        response = self._get(f'/iserver/services/{service_name}.json')
        return response.json()

    # ========== 地图服务 ==========

    def get_map(self, map_name: str) -> Dict:
        """
        获取地图信息

        Args:
            map_name: 地图服务名称

        Returns:
            地图信息
        """
        response = self._get(f'/iserver/services/map-{map_name}/rest/maps/{map_name}.json')
        return response.json()

    def get_map_image(
        self,
        service_name: str,
        bounds: Optional[Tuple[float, float, float, float]] = None,
        width: int = 1024,
        height: int = 512,
        transparent: bool = False,
        layers: Optional[List[str]] = None
    ) -> bytes:
        """
        获取地图图片

        Args:
            service_name: 地图服务名称
            bounds: 地图范围 (minX, minY, maxX, maxY)
            width: 图片宽度 (像素)
            height: 图片高度 (像素)
            transparent: 是否透明背景
            layers: 要显示的图层列表

        Returns:
            图片数据 (bytes)
        """
        params = {
            'width': width,
            'height': height,
            'transparent': transparent
        }

        if bounds:
            params['bounds'] = f'{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}'

        if layers:
            params['layers'] = 'show:' + ','.join(layers)

        response = self._get(f'/iserver/services/{service_name}/rest/maps/{service_name}/image.png', params=params)
        return response.content

    # ========== 数据服务 ==========

    def query_data(
        self,
        service_name: str,
        dataset_name: str,
        filter: Optional[str] = None,
        return_geometry: bool = True,
        fields: Optional[List[str]] = None,
        from_index: int = 0,
        to_index: int = 19
    ) -> Dict:
        """
        查询数据

        Args:
            service_name: 数据服务名称
            dataset_name: 数据集名称
            filter: 过滤条件 (SQL WHERE 子句)
            return_geometry: 是否返回几何信息
            fields: 要返回的字段列表
            from_index: 起始索引
            to_index: 结束索引

        Returns:
            查询结果
        """
        params = {
            'datasetNames': dataset_name,
            'returnGeometry': return_geometry,
            'fromIndex': from_index,
            'toIndex': to_index
        }

        if filter:
            params['filter'] = filter

        if fields:
            params['fields'] = ','.join(fields)

        response = self._get(f'/iserver/services/{service_name}/rest/data/featureResults.json', params=params)
        return response.json()

    def get_features_by_ids(
        self,
        service_name: str,
        dataset_name: str,
        ids: List[int],
        return_geometry: bool = True
    ) -> Dict:
        """
        根据 ID 获取要素

        Args:
            service_name: 数据服务名称
            dataset_name: 数据集名称
            ids: 要查询的 ID 列表
            return_geometry: 是否返回几何信息

        Returns:
            要素数据
        """
        params = {
            'datasetNames': dataset_name,
            'getFeatureMode': 'ID',
            'ids': ','.join(map(str, ids)),
            'returnGeometry': return_geometry
        }

        response = self._get(f'/iserver/services/{service_name}/rest/data/featureResults.json', params=params)
        return response.json()

    # ========== 分析服务 ==========

    def execute_buffer_analysis(
        self,
        input_data: Dict,
        distance: float,
        unit: str = "METER",
        result_name: str = "buffer_result"
    ) -> Dict:
        """
        执行缓冲区分析

        Args:
            input_data: 输入数据
            distance: 缓冲距离
            unit: 距离单位 (METER, KILOMETER, MILE, YARD)
            result_name: 结果名称

        Returns:
            分析结果
        """
        params = {
            'analystName': 'buffer',
            'parameter': json.dumps({
                'input': input_data,
                'bufferDistance': distance,
                'bufferDistanceUnit': unit,
                'resultSetting': {
                    'resultName': result_name,
                    'expectCount': 1000
                }
            })
        }

        response = self._get('/iserver/services/spatialanalyst/rest/analyst/buffer', params=params)
        return response.json()

    def execute_overlay_analysis(
        self,
        source_dataset: str,
        overlay_dataset: str,
        operation: str = "INTERSECT",
        tolerance: float = 0.0001
    ) -> Dict:
        """
        执行叠加分析

        Args:
            source_dataset: 源数据集
            overlay_dataset: 叠加数据集
            operation: 叠加操作 (INTERSECT, UNION, IDENTITY, ERASE, UPDATE, XOR)
            tolerance: 容限

        Returns:
            分析结果
        """
        params = {
            'analystName': 'overlay',
            'parameter': json.dumps({
                'sourceDataset': source_dataset,
                'overlayDataset': overlay_dataset,
                'operation': operation,
                'tolerance': tolerance
            })
        }

        response = self._get('/iserver/services/spatialanalyst/rest/analyst/overlay', params=params)
        return response.json()

    # ========== WMS/WMTS ==========

    def get_wms_capabilities(self, service_name: str) -> str:
        """
        获取 WMS 能力文档

        Args:
            service_name: 服务名称

        Returns:
            WMS XML
        """
        params = {'request': 'GetCapabilities', 'service': 'WMS'}
        response = self._get(f'/iserver/services/{service_name}/wms', params=params)
        return response.text

    def get_wmts_capabilities(self, service_name: str) -> str:
        """
        获取 WMTS 能力文档

        Args:
            service_name: 服务名称

        Returns:
            WMTS XML
        """
        params = {'request': 'GetCapabilities', 'service': 'WMTS'}
        response = self._get(f'/iserver/services/{service_name}/wmts', params=params)
        return response.text

    # ========== 实用方法 ==========

    def ping(self) -> bool:
        """
        测试服务器连接

        Returns:
            是否连接成功
        """
        try:
            response = self._get('/iserver/services', timeout=5)
            return response.status_code == 200
        except Exception:
            return False


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例 1: 初始化客户端
    client = iServerClient(
        server_url="http://localhost:8090",
        token="your_token_here"
    )

    # 测试连接
    if client.ping():
        print("✓ 服务器连接成功")

    # 示例 2: 获取服务列表
    services = client.list_services()
    print(f"服务列表: {[s['name'] for s in services]}")

    # 示例 3: 获取地图信息
    map_info = client.get_map("world")
    print(f"地图名称: {map_info['name']}")
    print(f"坐标系: {map_info['prjCoordSys']['name']}")

    # 示例 4: 查询数据
    data = client.query_data(
        service_name="data-world",
        dataset_name="Capitals",
        filter="POP > 10000000",
        fields=["NAME", "POP"],
        from_index=0,
        to_index=10
    )
    print(f"查询到 {len(data['features'])} 个要素")
    for feature in data['features']:
        print(f"  {feature['properties']['NAME']}: {feature['properties']['POP']}")
