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