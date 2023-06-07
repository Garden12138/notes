## 使用 docker 部署 mysql

> 拉取镜像
  
  ```bash
  docker pull mysql:5.7
  ```

> 运行测试容器，拷贝配置文件
  
  ```bash
  docker run --name mysql-test -d -e MYSQL_ROOT_PASSWORD=garden520 mysql:5.7  
  docker cp mysql-test:/etc/my.cnf /data/mysql/conf && docker stop mysql-test && docker rm mysql-test
  ```

> 运行容器

  ```bash
  docker run --name mysql \
  --restart=always \
  --privileged=true \
  -d \
  -p 13306:3306 \
  -v /data/mysql/data:/var/lib/mysql \
  -v /data/mysql/conf:/etc/mysql/conf.d \
  -v /data/mysql/log:/var/log/mysql \
  -e TZ=Asia/Shanghai \
  -e MYSQL_ROOT_PASSWORD=garden520 \
  mysql:5.7 \
  --character-set-server=utf8mb4 \
  --collation-server=utf8mb4_general_ci
  ```