## 使用 docker 部署 nginx

> 拉取镜像

  ```bash
  docker pull nginx:latest
  ```

> 运行测试容器，拷贝配置文件

  ```bash
  docker run --name nginx-test -d nginx:latest  
  docker cp nginx-test:/etc/nginx /data && docker cp nginx-test:/usr/share/nginx/html /data/nginx && docker stop nginx-test && docker rm nginx-test
  ```

> 运行容器

  ```bash
  docker run --name nginx --restart=always --privileged=true -p 4000:80 -v /data/nginx:/etc/nginx -v /data/nginx/html:/usr/share/nginx/html -v /data/nginx/logs:/var/log/nginx -d nginx:latest
  ```