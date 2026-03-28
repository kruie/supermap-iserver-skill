# SuperMap iServer REST API 参考文档

## 概述

SuperMap iServer 提供完整的 RESTful API,支持地图服务、数据服务、分析服务、三维服务等各类操作。

## 基础信息

### 服务器地址

```
http://localhost:8090
https://your-server:8443
```

### 认证方式

#### 1. 令牌认证 (推荐)

```bash
# 获取令牌
POST /iserver/security/token
{
  "username": "admin",
  "password": "supermap"
}

# 返回
{
  "token": "your_token_string",
  "expireTime": "2026-03-28T22:00:00Z"
}

# 使用令牌
GET /iserver/services?token=your_token_string
# 或
Header: token: your_token_string
```

#### 2. 基本认证

```bash
# Header
Authorization: Basic base64(username:password)
```

### 响应格式

所有 API 返回 JSON 格式,成功响应:

```json
{
  "succeed": true,
  "newResourceID": "service_name",
  "postResultType": "CreateChild",
  "childResourceConfigs": [...]
}
```

错误响应:

```json
{
  "succeed": false,
  "error": {
    "code": 400,
    "errorMsg": "参数错误"
  }
}
```

---

## 服务管理 API

### 1. 获取服务列表

```http
GET /iserver/services
```

**响应示例**:

```json
{
  "services": [
    {
      "name": "map-world",
      "type": "map",
      "state": "RUNNING"
    },
    {
      "name": "data-world",
      "type": "data",
      "state": "RUNNING"
    }
  ]
}
```

### 2. 获取服务信息

```http
GET /iserver/services/{service_name}.json
```

**参数**:
- `service_name`: 服务名称

### 3. 启动服务

```http
POST /iserver/manager/services/{service_name}.json
{
  "action": "start"
}
```

### 4. 停止服务

```http
POST /iserver/manager/services/{service_name}.json
{
  "action": "stop"
}
```

### 5. 重启服务

```http
POST /iserver/manager/services/{service_name}.json
{
  "action": "restart"
}
```

---

## 地图服务 API

### 1. 获取地图信息

```http
GET /iserver/services/map-{map_name}/rest/maps/{map_name}.json
```

**响应示例**:

```json
{
  "name": "World",
  "prjCoordSys": {
    "type": "PCS",
    "name": "EPSG:4326",
    "epsgCode": 4326
  },
  "bounds": {
    "left": -180,
    "bottom": -90,
    "right": 180,
    "top": 90
  },
  "scale": 1.0,
  "viewer": {
    "width": 1024,
    "height": 512
  },
  "layers": [
    {
      "name": "layer1",
      "caption": "图层1",
      "type": "VECTOR",
      "visible": true
    }
  ]
}
```

### 2. 获取地图图片

```http
GET /iserver/services/{service_name}/rest/maps/{map_name}/image.png
```

**参数**:
- `width`: 图片宽度 (像素)
- `height`: 图片高度 (像素)
- `bounds`: 地图范围 `minX,minY,maxX,maxY`
- `center`: 中心点 `x,y`
- `scale`: 比例尺
- `transparent`: 是否透明背景 (true/false)
- `layers`: 要显示的图层 `show:layer1,layer2`
- `redirect`: 是否重定向 (true/false)

**示例**:

```bash
# 按范围获取
GET /iserver/services/map-world/rest/maps/World/image.png?width=1024&height=512&bounds=-180,-90,180,90

# 按中心点和比例尺获取
GET /iserver/services/map-world/rest/maps/World/image.png?center=0,0&scale=1.0&width=1024&height=512
```

### 3. 获取图层信息

```http
GET /iserver/services/{service_name}/rest/maps/{map_name}/layers/{layer_name}.json
```

---

## 数据服务 API

### 1. 查询要素

```http
GET /iserver/services/{service_name}/rest/data/featureResults.json
```

**参数**:
- `datasetNames`: 数据集名称
- `returnGeometry`: 是否返回几何 (true/false)
- `fromIndex`: 起始索引
- `toIndex`: 结束索引
- `filter`: 过滤条件 (SQL WHERE 子句)
- `fields`: 要返回的字段 (逗号分隔)
- `getFeatureMode`: 查询模式 (ID, FILTER, SQL)

**示例**:

```bash
# 查询所有要素
GET /iserver/services/data-world/rest/data/featureResults.json?datasetNames=Capitals&returnGeometry=true&fromIndex=0&toIndex=19

# 带过滤条件查询
GET /iserver/services/data-world/rest/data/featureResults.json?datasetNames=Capitals&filter=POP > 10000000

# 指定字段查询
GET /iserver/services/data-world/rest/data/featureResults.json?datasetNames=Capitals&fields=NAME,POP,CAPITAL
```

**响应示例**:

```json
{
  "featureCount": 19,
  "features": [
    {
      "fieldNames": ["NAME", "POP", "CAPITAL"],
      "fieldValues": ["北京", "21710000", "北京"],
      "geometry": {"type": "Point", "coordinates": [116.4, 39.9]}
    }
  ],
  "recordset": {
    "datasetName": "Capitals",
    "fieldInfos": [
      {"name": "NAME", "type": "TEXT"},
      {"name": "POP", "type": "INT32"},
      {"name": "CAPITAL", "type": "TEXT"}
    ]
  }
}
```

### 2. 按 ID 查询要素

```http
GET /iserver/services/{service_name}/rest/data/featureResults.json?getFeatureMode=ID&ids=1,2,3
```

### 3. 获取数据集信息

```http
GET /iserver/services/{service_name}/rest/data/datasources/{datasource_name}/datasets.json
```

---

## 分析服务 API

### 1. 缓冲区分析

```http
GET /iserver/services/spatialanalyst/rest/analyst/buffer
```

**参数**:
- `analystName`: 分析名称 (buffer)
- `parameter`: JSON 格式的分析参数

**参数格式**:

```json
{
  "input": {
    "type": "dataset",
    "dataset": "world:Capitals"
  },
  "bufferDistance": 0.5,
  "bufferDistanceUnit": "DEGREE",
  "resultSetting": {
    "resultName": "buffer_result",
    "expectCount": 1000
  }
}
```

**示例**:

```bash
GET /iserver/services/spatialanalyst/rest/analyst/buffer?analystName=buffer&parameter={"input":{"type":"dataset","dataset":"world:Capitals"},"bufferDistance":0.5,"bufferDistanceUnit":"DEGREE","resultSetting":{"resultName":"buffer_result","expectCount":1000}}
```

### 2. 叠加分析

```http
GET /iserver/services/spatialanalyst/rest/analyst/overlay
```

**参数**:

```json
{
  "sourceDataset": "world:Countries",
  "overlayDataset": "world:Rivers",
  "operation": "INTERSECT",
  "tolerance": 0.0001
}
```

**操作类型**:
- `INTERSECT`: 交集
- `UNION`: 并集
- `IDENTITY`: 恒定
- `ERASE`: 擦除
- `UPDATE`: 更新
- `XOR`: 异或

### 3. 核密度分析

```http
GET /iserver/services/spatialanalyst/rest/analyst/density
```

**参数**:

```json
{
  "input": {
    "type": "dataset",
    "dataset": "world:Capitals"
  },
  "radius": 100,
  "radiusUnit": "METER",
  "cellSize": 0.1,
  "cellSizeUnit": "DEGREE",
  "resultSetting": {
    "resultName": "density_result"
  }
}
```

---

## 三维服务 API

### 1. 获取三维场景信息

```http
GET /iserver/services/3D-{scene_name}/rest/scene/sceneInfos.json
```

### 2. 获取三维图层列表

```http
GET /iserver/services/3D-{scene_name}/rest/scene/layers.json
```

### 3. 获取 S3M 图层信息

```http
GET /iserver/services/3D-{scene_name}/rest/realspace/datas/{layer_name}.json
```

---

## WMS 服务

### 1. GetCapabilities

```http
GET /iserver/services/{service_name}/wms?request=GetCapabilities&service=WMS
```

### 2. GetMap

```http
GET /iserver/services/{service_name}/wms?service=WMS&version=1.3.0&request=GetMap&layers={layer_name}&styles=&crs=EPSG:4326&bbox=-180,-90,180,90&width=1024&height=512&format=image/png
```

**参数**:
- `layers`: 图层名称 (逗号分隔)
- `styles`: 样式 (逗号分隔)
- `crs`: 坐标系 (如 EPSG:4326)
- `bbox`: 边界框 `minX,minY,maxX,maxY`
- `width`: 图片宽度
- `height`: 图片高度
- `format`: 输出格式 (image/png, image/jpeg)

### 3. GetFeatureInfo

```http
GET /iserver/services/{service_name}/wms?service=WMS&version=1.3.0&request=GetFeatureInfo&layers={layer_name}&query_layers={layer_name}&crs=EPSG:4326&bbox=-180,-90,180,90&width=1024&height=512&format=image/png&info_format=application/json&i=512&j=256
```

**参数**:
- `query_layers`: 查询的图层
- `info_format`: 信息格式 (application/json, text/plain)
- `i`: 列索引 (像素)
- `j`: 行索引 (像素)

---

## WMTS 服务

### 1. GetCapabilities

```http
GET /iserver/services/{service_name}/wmts?request=GetCapabilities&service=WMTS
```

### 2. GetTile

```http
GET /iserver/services/{service_name}/wmts?service=WMTS&version=1.0.0&request=GetTile&layer={layer_name}&style=default&tilematrixset={matrix_set}&tilematrix={level}&tilerow={row}&tilecol={col}&format=image/png
```

**参数**:
- `layer`: 图层名称
- `style`: 样式名称
- `tilematrixset`: 瓦片矩阵集
- `tilematrix`: 瓦片矩阵 (层级)
- `tilerow`: 瓦片行号
- `tilecol`: 瓦片列号
- `format`: 格式

---

## WFS 服务

### 1. GetCapabilities

```http
GET /iserver/services/{service_name}/wfs?request=GetCapabilities&service=WFS
```

### 2. DescribeFeatureType

```http
GET /iserver/services/{service_name}/wfs?request=DescribeFeatureType&service=WFS&typeName={dataset_name}
```

### 3. GetFeature

```http
GET /iserver/services/{service_name}/wfs?request=GetFeature&service=WFS&version=2.0.0&typeName={dataset_name}&outputFormat=application/json&bbox=-180,-90,180,90
```

**参数**:
- `typeName`: 数据集名称
- `outputFormat`: 输出格式 (application/json, text/xml; subtype=gml/3.1.1)
- `bbox`: 边界框
- `maxFeatures`: 最大要素数

---

## 错误码参考

| 错误码 | 说明 |
|-------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 (令牌无效或过期) |
| 403 | 禁止访问 (权限不足) |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 使用示例

### Python 示例

```python
import requests

# 基础配置
SERVER_URL = "http://localhost:8090"
TOKEN = "your_token_here"

# 1. 获取服务列表
response = requests.get(
    f"{SERVER_URL}/iserver/services",
    headers={"token": TOKEN}
)
services = response.json()

# 2. 获取地图信息
response = requests.get(
    f"{SERVER_URL}/iserver/services/map-world/rest/maps/World.json",
    headers={"token": TOKEN}
)
map_info = response.json()

# 3. 查询数据
response = requests.get(
    f"{SERVER_URL}/iserver/services/data-world/rest/data/featureResults.json",
    params={
        "datasetNames": "Capitals",
        "filter": "POP > 10000000",
        "returnGeometry": True,
        "fromIndex": 0,
        "toIndex": 10
    },
    headers={"token": TOKEN}
)
features = response.json()

# 4. 执行缓冲区分析
response = requests.get(
    f"{SERVER_URL}/iserver/services/spatialanalyst/rest/analyst/buffer",
    params={
        "analystName": "buffer",
        "parameter": json.dumps({
            "input": {"type": "dataset", "dataset": "world:Capitals"},
            "bufferDistance": 0.5,
            "bufferDistanceUnit": "DEGREE",
            "resultSetting": {
                "resultName": "buffer_result",
                "expectCount": 1000
            }
        })
    },
    headers={"token": TOKEN}
)
result = response.json()
```

### JavaScript 示例

```javascript
// 使用 fetch API
const SERVER_URL = "http://localhost:8090";
const TOKEN = "your_token_here";

// 获取服务列表
fetch(`${SERVER_URL}/iserver/services`, {
  headers: { token: TOKEN }
})
  .then(res => res.json())
  .then(data => console.log(data));

// 获取地图图片
const mapImage = `${SERVER_URL}/iserver/services/map-world/rest/maps/World/image.png?width=1024&height=512&bounds=-180,-90,180,90`;
document.getElementById("map").src = mapImage;
```

---

## 相关文档

- [SuperMap iServer 官方文档](https://help.supermap.com/iServer/zh/)
- [iClient JavaScript](https://iclient.supermap.io/)
- [OpenLayers + SuperMap](https://openlayers.org/en/latest/doc/)
- [Leaflet + SuperMap](https://leafletjs.com/)
