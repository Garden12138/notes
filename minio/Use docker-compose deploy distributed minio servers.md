## 使用 docker-compose 部署分布式 minio servers

> 前期准备

* ```docker version```为24.0.2
* ```docker-compose version```为v2.4.1

> 集群组件

* nginx
* minio1（disk1、disk2）
* minio2（disk1、disk2）
* minio3（disk1、disk2）
* minio4（disk1、disk2）

> 新增```docker-compose.yaml```文件并编写配置：

  ```bash
  version: '3.7'

  # Settings and configurations that are common for all containers
  x-minio-common: &minio-common
    image: quay.io/minio/minio:RELEASE.2023-10-25T06-33-25Z
    command: server --console-address ":9001" http://minio{1...4}/data{1...2}
    expose:
      - "9000"
      - "9001"
  # environment:
    # MINIO_ROOT_USER: minioadmin
    # MINIO_ROOT_PASSWORD: minioadmin
    # MINIO_SERVER_URL: ${SERVER_API_HOST}
    # MINIO_BROWSER_REDIRECT_URL: ${WEB_CONSOLE_HOST}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
    interval: 30s
    timeout: 20s
    retries: 3

  # starts 4 docker containers running minio server instances.
  # using nginx reverse proxy, load balancing, you can access
  # it through port 9000.
  services:
    minio1:
      <<: *minio-common
      hostname: minio1
      volumes:
        - data1-1:/data1
        - data1-2:/data2

    minio2:
      <<: *minio-common
      hostname: minio2
      volumes:
        - data2-1:/data1
        - data2-2:/data2

    minio3:
      <<: *minio-common
      hostname: minio3
      volumes:
        - data3-1:/data1
        - data3-2:/data2

    minio4:
      <<: *minio-common
      hostname: minio4
      volumes:
        - data4-1:/data1
        - data4-2:/data2

    nginx:
      image: nginx:1.19.2-alpine
      hostname: nginx
      volumes:
        - ./nginx.conf:/etc/nginx/nginx.conf:ro
      ports:
        - "9000:9000"
        - "9001:9001"
      depends_on:
        - minio1
        - minio2
        - minio3
        - minio4

  ## By default this config uses default local driver,
  ## For custom volumes replace with volume driver configuration.
  volumes:
    data1-1:
    data1-2:
    data2-1:
    data2-2:
    data3-1:
    data3-2:
    data4-1:
    data4-2:
  ```

  * 启动参数```http://minio{1...4}/data{1...2}```代表集群节点```minio1-4```分别的硬盘路径```data1-2```。
  * 环境变量```MINIO_SERVER_URL```与```MINIO_BROWSER_REDIRECT_URL```分别为设置访问```Minio API```的域名（9000端口）与访问```Minio Web Console```的域名（9001），这两个环境变量可让控制台的分享功能调用域名分享，而不是自动获取的内网```ip```地址或容器```ip```地址。在集群中，应对应```Nginx```实例的9000与9001端口。
  * 文件中使用卷标```volumes```方式，默认生成的挂载目录为```/var/lib/docker/volumes/${compose_parentdirname}_${volume_name}/_data```，如```/var/lib/docker/volumes/minio-distributed_data1-1/_data```，可通过命令```docker volume inspect ${compose_parentdirname}_${volume_name}```查看具体挂载目录。

> 新增```nginx.conf```文件并编写配置：
  
  ```bash
  user  nginx;
  worker_processes  auto;

  error_log  /var/log/nginx/error.log warn;
  pid        /var/run/nginx.pid;

  events {
      worker_connections  4096;
  }

  http {
      include       /etc/nginx/mime.types;
      default_type  application/octet-stream;

      log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                        '$status $body_bytes_sent "$http_referer" '
                        '"$http_user_agent" "$http_x_forwarded_for"';

      access_log  /var/log/nginx/access.log  main;
      sendfile        on;
      keepalive_timeout  65;

      # include /etc/nginx/conf.d/*.conf;

      upstream minio {
          server minio1:9000;
          server minio2:9000;
          server minio3:9000;
          server minio4:9000;
      }

      upstream console {
          ip_hash;
          server minio1:9001;
          server minio2:9001;
          server minio3:9001;
          server minio4:9001;
      }

      server {
          listen       9000;
          listen  [::]:9000;
          server_name  localhost;

          # To allow special characters in headers
          ignore_invalid_headers off;
          # Allow any size file to be uploaded.
          # Set to a value such as 1000m; to restrict file size to a specific value
          client_max_body_size 10m;
          # To disable buffering
          proxy_buffering off;
          proxy_request_buffering off;

          location / {
              proxy_set_header Host $http_host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto $scheme;

              proxy_connect_timeout 300;
              # Default is HTTP/1, keepalive is only enabled in HTTP/1.1
              proxy_http_version 1.1;
              proxy_set_header Connection "";
              chunked_transfer_encoding off;

              proxy_pass http://minio;
          }
      }

      server {
          listen       9001;
          listen  [::]:9001;
          server_name  localhost;

          # To allow special characters in headers
          ignore_invalid_headers off;
          # Allow any size file to be uploaded.
          # Set to a value such as 1000m; to restrict file size to a specific value
          client_max_body_size 10m;
          # To disable buffering
          proxy_buffering off;
          proxy_request_buffering off;

          location / {
              proxy_set_header Host $http_host;
              proxy_set_header X-Real-IP $remote_addr;
              proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
              proxy_set_header X-Forwarded-Proto $scheme;
              proxy_set_header X-NginX-Proxy true;

              # This is necessary to pass the correct IP to be hashed
              real_ip_header X-Real-IP;
              
              proxy_connect_timeout 300;
              
              # To support websocket
              proxy_http_version 1.1;
              proxy_set_header Upgrade $http_upgrade;
              proxy_set_header Connection "upgrade";
            
              chunked_transfer_encoding off;

              proxy_pass http://console;
          }
      }
  }
  ```

> 编排容器

  ```bash
  docker-compose pull
  docker-compose -d up
  ```

> 参考文献

* [Deploy MinIO on Docker Compose](https://github.com/minio/minio/blob/master/docs/orchestration/docker-compose/README.md)