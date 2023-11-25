## 在不同的云服务器间部署分布式 minio servers

> 前期准备

* 三台2核4```GB```的```Cenos7.6```操作系统的云服务器，其中两台内网云服务器用于搭建```minio1、minio2```实例，一台包含公网与内网云服务器用于搭建```nginx```，实现负载均衡.

* 每台服务器系统包含的```docker version```为24.0.2，```docker-compose version```为v2.4.1

> 集群各组件示意图

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minio/Snipaste_2023-11-25_15-02-10.png)

> 分别编写minio1、minio2以及nginx的docker-compose文件

  ```bash
  # minio1的docker-compose.yaml
  version: '3.7'
  services:
  minio1:
    image: quay.io/minio/minio:RELEASE.2023-10-25T06-33-25Z
    volumes:
      - /data/minio-distributed/data1:/data1
      - /data/minio-distributed/data2:/data2
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio@2023
    network_mode: host
    command: server --console-address ":9001" http://minio{1...2}/data{1...2}
    extra_hosts:
      - "minio1:10.0.12.13"
      - "minio2:10.0.12.17"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
  ```
  
  配置```network_mode```为```host```，表示使用```host```网络模式，多集群改设置必须为```host```，否则磁盘会找不到。配置```extra_hosts```为设置容器中访问```minio1..2```的内网```ip```地址，此处不能为公网```ip```地址。

  ```bash
  # minio2的docker-compose.yaml
  version: '3.7'
  services:
  minio2:
    image: quay.io/minio/minio:RELEASE.2023-10-25T06-33-25Z
    volumes:
      - /data/minio-distributed/data1:/data1
      - /data/minio-distributed/data2:/data2
    environment:
      MINIO_ROOT_USER: minio
      MINIO_ROOT_PASSWORD: minio@2023
    network_mode: host
    command: server --console-address ":9001" http://minio{1...2}/data{1...2}
    extra_hosts:
      - "minio1:10.0.12.13"
      - "minio2:10.0.12.17"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3
  ```

  ```bash
  version: '3.7'
  services:
  nginx:
    image: nginx:1.19.2-alpine
    hostname: nginx
    # 本示例中的ngix服务器与其他两台服务器内网不通，故使用公网模拟
    extra_hosts:
      - "minio1:159.75.138.212"
      - "minio2:175.178.78.209"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    ports:
      - "9000:9000"
      - "9001:9001" 
  ```

> 编写nginx.conf
  
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
      }

      upstream console {
          ip_hash;
          server minio1:9001;
          server minio2:9001;
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

> 在三台服务器内分配执行minio1、minio2以及nginx的docker-compose启动命令
  
  ```bash
  docker-compose up -d
  ```

> 参考文献

* [使用 docker-compose 部署分布式 minio servers](https://gitee.com/FSDGarden/learn-note/blob/master/minio/Use%20docker-compose%20deploy%20distributed%20minio%20servers.md)
* [03. minio 多机集群](https://www.jianshu.com/p/f85286a64c32)
* [[not our bug] Unable to read 'format.json' from http://ip:9000/data-mi/data1: Expected 'storage' API version 'v20', instead found 'a1', please upgrade the servers](https://github.com/minio/minio/issues/10529)

