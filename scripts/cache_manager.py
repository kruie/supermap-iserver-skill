"""
SuperMap iServer 缓存管理工具

提供缓存清除、预生成、缓存策略配置等功能。
"""

import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CacheInfo:
    """缓存信息数据类"""
    service_name: str
    cache_type: str
    cache_size: int  # 字节
    tile_count: int
    last_generated: str
    cache_path: str


class CacheManager:
    """iServer 缓存管理器"""

    def __init__(
        self,
        server_url: str,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化缓存管理器

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

    def _post(self, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """发送 POST 请求"""
        url = f"{self.server_url}{endpoint}"
        response = self.session.post(url, json=json_data, timeout=self.timeout)
        response.raise_for_status()
        return response

    # ========== 缓存清除 ==========

    def clear_cache(
        self,
        service_name: str,
        cache_type: str = "all",
        bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict:
        """
        清除缓存

        Args:
            service_name: 服务名称
            cache_type: 缓存类型 (all, map, image, vector)
            bounds: 清除范围 (minX, minY, maxX, maxY) (可选)

        Returns:
            清除结果
        """
        data = {'cacheType': cache_type}

        if bounds:
            data['bounds'] = f'{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}'

        response = self._post(
            f'/iserver/manager/clearcache/{service_name}.json',
            json_data=data
        )
        return response.json()

    def clear_all_cache(self) -> Dict[str, bool]:
        """
        清除所有服务的缓存

        Returns:
            清除结果字典 {service_name: success}
        """
        response = self._get('/iserver/manager/services.json')
        services = response.json()

        results = {}

        for service in services:
            service_name = service['name']
            try:
                result = self.clear_cache(service_name, cache_type='all')
                results[service_name] = True
                print(f"✓ {service_name}: 缓存清除成功")
            except Exception as e:
                results[service_name] = False
                print(f"✗ {service_name}: 缓存清除失败 - {e}")

        return results

    # ========== 缓存预生成 ==========

    def pre_generate_cache(
        self,
        service_name: str,
        scales: List[float],
        bounds: Optional[Tuple[float, float, float, float]] = None,
        layers: Optional[List[str]] = None,
        image_format: str = "PNG"
    ) -> Dict:
        """
        预生成缓存

        Args:
            service_name: 服务名称
            scales: 比例尺列表
            bounds: 生成范围 (minX, minY, maxX, maxY) (可选)
            layers: 要生成的图层列表 (可选)
            image_format: 图片格式 (PNG, JPG, WEBP)

        Returns:
            生成结果
        """
        data = {
            'scales': scales,
            'imageFormat': image_format
        }

        if bounds:
            data['bounds'] = f'{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}'

        if layers:
            data['layers'] = ','.join(layers)

        response = self._post(
            f'/iserver/manager/precache/{service_name}.json',
            json_data=data
        )
        return response.json()

    def pre_generate_cache_full(
        self,
        service_name: str,
        min_scale: float,
        max_scale: float,
        scale_levels: int = 20,
        bounds: Optional[Tuple[float, float, float, float]] = None
    ) -> Dict:
        """
        预生成完整缓存 (从最小到最大比例尺)

        Args:
            service_name: 服务名称
            min_scale: 最小比例尺 (如 1:5000000)
            max_scale: 最大比例尺 (如 1:5000)
            scale_levels: 比例尺级数
            bounds: 生成范围 (可选)

        Returns:
            生成结果
        """
        # 计算比例尺列表 (指数分布)
        scales = []
        for i in range(scale_levels):
            ratio = i / (scale_levels - 1)
            scale = min_scale * (1 - ratio) + max_scale * ratio
            scales.append(scale)

        return self.pre_generate_cache(service_name, scales, bounds)

    # ========== 缓存策略 ==========

    def configure_cache_strategy(
        self,
        service_name: str,
        enable_cache: bool = True,
        cache_size_limit: Optional[int] = None,
        tile_size: int = 256,
        compression: bool = True,
        compression_quality: int = 80
    ) -> Dict:
        """
        配置缓存策略

        Args:
            service_name: 服务名称
            enable_cache: 是否启用缓存
            cache_size_limit: 缓存大小限制 (MB)
            tile_size: 瓦片大小 (像素)
            compression: 是否启用压缩
            compression_quality: 压缩质量 (0-100)

        Returns:
            配置结果
        """
        data = {
            'serviceName': service_name,
            'enableCache': enable_cache,
            'tileSize': tile_size,
            'compression': compression,
            'compressionQuality': compression_quality
        }

        if cache_size_limit:
            data['cacheSizeLimit'] = cache_size_limit

        response = self._post(
            '/iserver/manager/cache/strategy',
            json_data=data
        )
        return response.json()

    def get_cache_strategy(self, service_name: str) -> Dict:
        """
        获取缓存策略

        Args:
            service_name: 服务名称

        Returns:
            缓存策略配置
        """
        response = self._get(
            '/iserver/manager/cache/strategy',
            params={'serviceName': service_name}
        )
        return response.json()

    # ========== 缓存信息 ==========

    def get_cache_info(self, service_name: str) -> CacheInfo:
        """
        获取缓存信息

        Args:
            service_name: 服务名称

        Returns:
            缓存信息对象
        """
        response = self._get(f'/iserver/manager/cache/{service_name}.json')
        data = response.json()

        return CacheInfo(
            service_name=data['serviceName'],
            cache_type=data['cacheType'],
            cache_size=data['cacheSize'],
            tile_count=data['tileCount'],
            last_generated=data['lastGenerated'],
            cache_path=data['cachePath']
        )

    def get_all_cache_info(self) -> List[CacheInfo]:
        """
        获取所有服务的缓存信息

        Returns:
            缓存信息列表
        """
        response = self._get('/iserver/manager/services.json')
        services = response.json()

        cache_infos = []

        for service in services:
            service_name = service['name']
            try:
                cache_info = self.get_cache_info(service_name)
                cache_infos.append(cache_info)
            except Exception as e:
                print(f"获取服务 {service_name} 缓存信息失败: {e}")

        return cache_infos

    # ========== 缓存统计 ==========

    def get_cache_statistics(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        cache_infos = self.get_all_cache_info()

        total_size = sum(info.cache_size for info in cache_infos)
        total_tiles = sum(info.tile_count for info in cache_infos)

        return {
            'total_services': len(cache_infos),
            'total_cache_size': total_size,
            'total_cache_size_mb': total_size / (1024 * 1024),
            'total_cache_size_gb': total_size / (1024 * 1024 * 1024),
            'total_tiles': total_tiles,
            'services': [
                {
                    'service_name': info.service_name,
                    'cache_type': info.cache_type,
                    'cache_size_mb': info.cache_size / (1024 * 1024),
                    'tile_count': info.tile_count,
                    'last_generated': info.last_generated
                }
                for info in cache_infos
            ]
        }


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例 1: 初始化缓存管理器
    cache_manager = CacheManager(
        server_url="http://localhost:8090",
        token="your_token_here"
    )

    # 示例 2: 清除服务缓存
    result = cache_manager.clear_cache(
        service_name="map-world",
        cache_type="all"
    )
    print(f"清除缓存: {result}")

    # 示例 3: 清除指定范围的缓存
    result = cache_manager.clear_cache(
        service_name="map-world",
        cache_type="map",
        bounds=(116.0, 39.0, 117.0, 40.0)  # 北京区域
    )
    print(f"清除指定范围缓存: {result}")

    # 示例 4: 预生成缓存
    result = cache_manager.pre_generate_cache(
        service_name="map-world",
        scales=[5000000, 1000000, 500000, 100000],
        bounds=(-180, -90, 180, 90)
    )
    print(f"预生成缓存: {result}")

    # 示例 5: 预生成完整缓存
    result = cache_manager.pre_generate_cache_full(
        service_name="map-world",
        min_scale=5000000,
        max_scale=5000,
        scale_levels=20
    )
    print(f"预生成完整缓存: {result}")

    # 示例 6: 配置缓存策略
    result = cache_manager.configure_cache_strategy(
        service_name="map-world",
        enable_cache=True,
        cache_size_limit=10240,  # 10GB
        tile_size=256,
        compression=True,
        compression_quality=80
    )
    print(f"配置缓存策略: {result}")

    # 示例 7: 获取缓存信息
    cache_info = cache_manager.get_cache_info("map-world")
    print(f"缓存信息:")
    print(f"  服务名: {cache_info.service_name}")
    print(f"  缓存类型: {cache_info.cache_type}")
    print(f"  缓存大小: {cache_info.cache_size / (1024 * 1024):.2f} MB")
    print(f"  瓦片数量: {cache_info.tile_count}")
    print(f"  最后生成: {cache_info.last_generated}")

    # 示例 8: 获取所有缓存信息
    all_cache_info = cache_manager.get_all_cache_info()
    print(f"\n所有服务缓存:")
    for info in all_cache_info:
        print(f"  - {info.service_name}: {info.cache_size / (1024 * 1024):.2f} MB ({info.tile_count} 瓦片)")

    # 示例 9: 获取缓存统计
    stats = cache_manager.get_cache_statistics()
    print(f"\n缓存统计:")
    print(f"  服务总数: {stats['total_services']}")
    print(f"  总缓存大小: {stats['total_cache_size_gb']:.2f} GB")
    print(f"  总瓦片数量: {stats['total_tiles']}")

    # 示例 10: 清除所有缓存
    results = cache_manager.clear_all_cache()
    print(f"\n清除所有缓存结果:")
    for service_name, success in results.items():
        print(f"  {service_name}: {'✓ 成功' if success else '✗ 失败'}")
