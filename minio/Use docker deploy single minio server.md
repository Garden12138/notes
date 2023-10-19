## 使用 docker 部署单机 minio server

docker pull minio/minio:latest

mkdir -p /data/minio/config & mkdir -p /data/minio/data


docker run \
  --name=minio \
  --restart=always \
  -d \
  -p 9000:9000 \
  -p 9001:9001 \
  -e "MINIO_ACCESS_KEY=minioadmin" \
  -e "MINIO_SECRET_KEY=minioadmin" \
  -v /home/minio/data:/data \
  -v /home/minio/config:/root/.minio \
  minio/minio:latest server /data --console-address ":9000" -address ":9001"

  http://114.132.78.39:9000/