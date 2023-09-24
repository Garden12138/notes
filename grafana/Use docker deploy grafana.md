## 使用 docker 部署 grafana

docker pull grafana/grafana:latest

docker run \
    --name=grafana \
    --restart=always \
    -d \
    -p 3000:3000 \
    grafana/grafana:latest