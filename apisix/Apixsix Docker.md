#### [下载安装Docker Compose](https://docs.docker.com/compose/install/)
```
-- 外网安装（https://docs.docker.com/compose/install/）
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
-- 离线安装（https://www.hangge.com/blog/cache/detail_2469.html）
```

#### [安装 Apache APISIX](https://apisix.apache.org/zh/docs/apisix/getting-started)
```
-- 外网
sudo yum install -y git
git clone https://github.com/apache/apisix-docker.git
-- 内网自行下载完apisix-docker，拷贝上传至服务器

cd apisix-docker/example
docker-compose -p docker-apisix up -d

curl "http://127.0.0.1:9080/apisix/admin/services/" -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1'
```

curl http://localhost:9080/apisix/admin/routes -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X GET

curl http://localhost:9080/apisix/admin/routes/404010792208302785 -H 'X-API-KEY: edd1c9f034335f136f87ad84b625c8f1' -X PATCH -i -d '
{
    "plugins":
    {
        "file-logger":
        {
            "path": "logs/file.log"
        }
    }
}'