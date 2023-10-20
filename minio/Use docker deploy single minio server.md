## 使用 docker 部署单机 minio server

> 拉取镜像

  ```bash
  docker pull minio/minio:latest
  ```

> 创建挂载目录

  ```bash
  mkdir -p /data/minio/config & mkdir -p /data/minio/data
  ```

  ```/data/minio/config```目录用于存放配置，```/data/minio/data```目录用于存储上传的文件。

> 运行容器

  ```bash
  docker run \
    --name=minio-server \
    --restart=always \
    -d \
    -p 9000:9000 \
    -p 9001:9001 \
    -e "MINIO_ACCESS_KEY=minioadmin" \
    -e "MINIO_SECRET_KEY=minioadmin" \
    -v /data/minio/data:/data \
    -v /data/minio/config:/root/.minio \
    minio/minio:latest server /data --console-address ":9000" -address ":9001"
  ```

  环境变量```MINIO_ACCESS_KEY```为```minio```登录账号；环境变量```MINIO_SECRET_KEY```为```minio```登录密码；启动参数```--console-address```以及```-address```分别设置控制台端口以及```API```端口。

> 验证服务是否启动成功

  * 浏览器输入访问地址，如```http://114.132.78.39:9000/```。

  * 创建一个```bucket```：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minio/Snipaste_2023-10-20_14-58-02.png)

    ```Bucket Name```表示设置```Bucket```名称；```Versioning```表示设置版本控制，允许在同一个键下保留同一个对象的多个版本；```Object Locking```表示设置对象锁定，防止对象被删除；```Quota```表示设置桶内的数据量。

  * 测试文件上传：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minio/Snipaste_2023-10-20_15-01-04.png)

> 参考文献

* [记录Minio Docker部署](https://juejin.cn/post/7206615325022224443)