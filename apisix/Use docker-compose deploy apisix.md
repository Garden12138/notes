## 使用 docker-compose 部署 apisix

> 下载源码

```bash
## 外网
sudo yum install -y git
git clone https://github.com/apache/apisix-docker.git
## 内网自行下载完 apisix-docker ，拷贝上传至服务器
```

> 编排容器

```bash
cd apisix-docker/example
docker-compose -p docker-apisix up -d
## 检查是否成功
curl "http://127.0.0.1:9080/apisix/admin/services/" -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1'
```

> 参考文献

* [官方文档](https://apisix.apache.org/zh/docs/apisix/getting-started)