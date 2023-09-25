## 使用 docker 部署 grafana

> 拉取镜像

  ```bash
  docker pull grafana/grafana:latest
  ```

> 运行容器

  ```bash
  docker run \
      --name=grafana \
      --restart=always \
      -d \
      -p 3000:3000 \
      grafana/grafana:latest
  ```