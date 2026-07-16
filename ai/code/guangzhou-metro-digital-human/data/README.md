# Dify sandbox 数据

广州地铁应用语义分析工作流依赖 7 个 JSON 文件：

| 文件 | 用途 |
|---|---|
| `alias.json` | 地点、站点和商户别名映射 |
| `poi.json` | POI 坐标及候选入口 |
| `stations.json` | 站点连接、线路、时间和换乘信息 |
| `amap_subway.json` | 地铁线路绘制数据 |
| `toilets.json` | 地铁站卫生间位置 |
| `ticket_guide.json` | 微信、支付宝和机器购票指南 |
| `food_list.json` | 美食列表 |

## 宿主机目录

当前部署将文件保存在：

```text
<dify-root>/docker/volumes/sandbox/data
```

Dify Compose 的 `sandbox` 服务增加以下挂载：

```yaml
services:
  sandbox:
    volumes:
      - ./volumes/sandbox/data:/var/sandbox/sandbox-python/app_data
```

工作流代码中的默认路径为：

```text
/app_data/alias.json
/app_data/poi.json
/app_data/stations.json
/app_data/amap_subway.json
/app_data/toilets.json
/app_data/ticket_guide.json
/app_data/food_list.json
```

## 只读校验

```bash
DATA_DIR="<dify-root>/docker/volumes/sandbox/data"

for name in \
  alias.json \
  poi.json \
  stations.json \
  amap_subway.json \
  toilets.json \
  ticket_guide.json \
  food_list.json
do
  test -s "$DATA_DIR/$name" || {
    echo "missing: $name" >&2
    exit 1
  }
  python3 -m json.tool "$DATA_DIR/$name" >/dev/null
done
```

不要将包含内部 POI、商户图片地址或业务兜底位置的数据直接发布到公开仓库。公开示例应替换地点、坐标和图片 URL，但保持字段结构不变。

