## docker compose使用

### 认识docker-compose配置

* 使用```docker-compose v3.8```版本，我们通过一个简单的示例子来了解```docker-compose```的使用方法：

  ```yaml
  # 指定 Docker Compose 文件格式版本
  version: '3.8'

  # 定义所有服务/容器
  services:
    # Web 服务 (Nginx)
    web:
      image: nginx:1.25-alpine  # 使用官方镜像
      container_name: my_web    # 自定义容器名称
      ports:
        - "80:80"               # 端口映射 (主机:容器)
        - "443:443"             # HTTPS 端口映射
      volumes:
        - ./nginx.conf:/etc/nginx/nginx.conf:ro  # 挂载自定义配置 (只读)
        - ./static:/usr/share/nginx/html         # 挂载静态资源
      networks:
        - app-network           # 加入自定义网络
      depends_on:
        - app                   # 依赖 app 服务
      restart: unless-stopped   # 重启策略 (除非手动停止)
      environment:              # 环境变量
        - TZ=Asia/Shanghai      # 时区设置
      healthcheck:              # 健康检查
        test: ["CMD", "curl", "-f", "http://localhost"]
        interval: 30s
        timeout: 10s
        retries: 3

    # Python 应用服务
    app:
      build: .  # 使用当前目录的 Dockerfile 构建镜像
      container_name: flask_app
      expose:
        - 5000  # 暴露端口 (不映射到主机)
      volumes:
        - ./app:/app            # 挂载应用代码 (开发环境热更新)
      networks:
        - app-network
      environment:
        - DATABASE_URL=postgresql://db_user:db_pass@db:5432/mydb
        - REDIS_HOST=redis
      depends_on:
        - db
        - redis

    # PostgreSQL 数据库服务
    db:
      image: postgres:15-alpine
      container_name: postgres_db
      volumes:
        - pgdata:/var/lib/postgresql/data  # 使用命名卷持久化数据
      networks:
        - app-network
      environment:
        - POSTGRES_USER=db_user
        - POSTGRES_PASSWORD=db_pass
        - POSTGRES_DB=mydb
      healthcheck:
        test: ["CMD-SHELL", "pg_isready -U db_user"]
        interval: 10s
        timeout: 5s
        retries: 5

    # Redis 服务
    redis:
      image: redis:7-alpine
      container_name: my_redis
      command: redis-server --requirepass redispass  # 启动命令
      volumes:
        - redisdata:/data  # 持久化存储
      networks:
        - app-network
      ports:
        - "6379:6379"  # 暴露 Redis 端口到主机

  # 定义网络 (创建自定义网络实现服务隔离)
  networks:
    app-network:
      driver: bridge  # 默认网络驱动
      ipam:
        config:
          - subnet: 172.20.0.0/24  # 自定义子网

  # 定义卷 (持久化数据管理)
  volumes:
    pgdata:    # PostgreSQL 数据卷
    redisdata: # Redis 数据卷
  ```

  服务（```services```）定义：

  * ```image```：指定使用的```Docker```镜像(优先于```build```)

  * ```build```：指定构建目录(```Dockerfile```所在路径)

  * ```container_name```: 自定义容器名称 (默认生成随机名称)

  * ```ports```：端口映射，格式为主机端口:容器端口

  * ```expose```： 仅暴露端口给其他服务 (不映射到主机)

  * ```volumes```：数据卷挂载：

    * ```././host/path:/container/path```：绝对路径挂载 (开发常用)

    * ```volume_name:/container/path```：命名卷挂载 (生产环境持久化)，可通过命令```docker volume ls```查看卷标，通过```docker volume inspect volume_name```查看卷详情（即实际存储路径）

  * ```networks```：指定加入的网络 (实现服务间通信)

  * ```depends_on```: 依赖于其他服务，控制启动顺序 (不保证服务完全就绪)

  * ```restart```：重启策略

    * ```no```：不重启

    * ```always```：总是重启

    * ```on-failure```：失败时重启

    * ```unless-stopped```：除非手动停止

  * ```environment```：设置环境变量(支持```KEY=VALUE```或列表)

  * ```healthcheck```：健康检查配置

    * ```test```：检查命令

    * ```interval```：检查间隔

    * ```timeout```：超时时间

    * ```retries```：失败重试次数

  网络（```networks```）配置：

  * 自定义网络，加入网络的容器可以互相访问，可以通过服务名进行通信：

    * ```driver```：网络驱动类型（```bridge```、```overlay```、```host```等）
    * ```ipam```：自定义子网配置

  卷（```volumes```）配置：

  * 命名卷，数据持久化独立于容器生命周期，默认存储在```/var/lib/docker/volumes```

### docker-compose常用命令

* 编排服务：

  ```bash
  docker-compose up [-d]
  ```

  ```-d```表示后台运行，如果需要指定compose文件，可以使用```-f```参数：

  ```bash
  docker-compose -f docker-compose.dev.yml up [-d]
  ```

  像上例```app```服务，如果代码更新，可指定服务重新构建后启动服务：

  ```bash
  docker-compose up [-d] --build app
  ```

* 查看服务状态：

  ```bash
  docker-compose ps [-a]
  ```

  ```-a```参数查看所有容器，包括停止的容器

* 停止服务：

  ```bash
  docker-compose stop
  ```

* 启动服务：

  ```bash
  docker-compose start
  ```

* 重启服务：

  ```bash
  docker-compose restart
  ```

* 删除服务（已停止的容器）：

  ```bash
  docker-compose rm
  ```

* 停止并删除所有容器以及相关网络：

  ```bash
  docker-compose down
  ```

* 进入容器：

  ```bash
  docker-compose exec [service] [command]
  ```

* 日志查看：

  ```bash
  docker-compose logs [-f] [service]
  ```

  ```-f```参数实时输出日志

* 在指定服务上执行命令：

  ```bash
  docker-compose run [service] [command]
  ```

* 设置指定服务运行的容器个数：

  ```bash
  docker-compose scale [service=num]
  ```

### 参考文献

* [Docker Compose](https://www.runoob.com/docker/docker-compose.html)
* [docker-compose-volumes的说明](https://www.jianshu.com/p/0beda3ece539)
* [docker-compose常用命令(持续更新中)](https://blog.51cto.com/u_15338614/3584341)