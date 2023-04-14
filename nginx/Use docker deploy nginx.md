## 使用 docker 部署 nginx

> 拉取镜像

  ```bash
  docker pull nginx:latest
  ```

> 运行测试容器，拷贝配置文件

  ```bash
  docker run --name nginx-test -d nginx:latest  
  mkdir -p /data/nginx/conf && docker cp nginx-test:/etc/nginx/nginx.conf /data/nginx/conf/ && docker stop nginx-test && docker rm nginx-test
  ```

> 运行容器

  ```bash
  docker run --name nginx --restart=always --privileged=true -p 4000:80 -v /data/nginx/conf/nginx.conf:/etc/nginx/nginx.conf:ro -v /data/nginx/conf/conf.d:/etc/nginx/conf.d:ro -v /data/nginx/html:/usr/share/nginx/html:rw -v /data/nginx/logs:/var/log/nginx -d nginx:latest
  ```