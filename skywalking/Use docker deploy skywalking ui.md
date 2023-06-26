## 使用 docker 部署 skywalking ui

> 拉取镜像
  
  ```bash
  docker pull apache/skywalking-ui:8.7.0
  ```

> 运行容器
  
  ```bash
  docker run --name skywalking-ui \
  --restart=always -d \
  -p 18080:8080 \
  -e SW_OAP_ADDRESS=http://114.132.78.39:12800 \
  -v /etc/localtime:/etc/localtime:ro \
  apache/skywalking-ui:8.7.0
  ```

> 访问地址
  
  ```bash
  http://114.132.78.39:18080/
  ```

* [『Skywalking』在Docker中快速部署Skywalking](https://developer.aliyun.com/article/987603)