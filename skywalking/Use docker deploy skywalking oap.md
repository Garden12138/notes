## 使用 docker 部署 skywalking oap

> 本文使用集成elasticsearch7的镜像

> 拉取镜像

  ```bash
  docker pull apache/skywalking-oap-server:8.7.0-es7
  ```

> 运行容器

  ```bash
  docker run --name skywalking-oap-server \
  --restart always -d \
  -p 11800:11800 \
  -p 12800:12800 \
  -e TZ=Asia/Shanghai \
  -e SW_STORAGE=elasticsearch7 \
  -e SW_STORAGE_ES_CLUSTER_NODES=114.132.78.39:9200 \
  -e SW_ES_USER=elastic \
  -e SW_ES_PASSWORD=garden520 \
  apache/skywalking-oap-server:8.7.0-es7
  ```

  映射端口11800为```agent```通信使用；映射端口12800为```ui```交互使用；环境变量```SW_STORAGE=elasticsearch7```为设置```skywalking```的存储方式为```es7```；环境变量```SW_STORAGE_ES_CLUSTER_NODES=114.132.78.39:9200```、```SW_ES_USER=elastic```以及```SW_ES_PASSWORD=garden520```为分别设置```skywalking```访问```es7```的可访问地址、账号以及密码。

> 参考文献

* [『Skywalking』在Docker中快速部署Skywalking](https://developer.aliyun.com/article/987603)