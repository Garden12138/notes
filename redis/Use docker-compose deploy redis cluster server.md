## 使用 docker-compose 部署 redis 集群服务

> 主从复制模式

* 该模式由主服务器与从服务器组成，经常使用“一主二从”的模式。主服务器可进行读写操作（客户端请求），当发生写操作时自动将写操作同步至从服务器，而从服务器接收并执行主服务器同步的写操作命令，但从服务器一般只进行读操作（客户端请求）。通过主从服务器间的读写分离以及复制方式实现多台服务器的数据一致性。

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/redis/Snipaste_2024-03-09_15-58-26.png)

* ```redis.conf```配置文件编写：
  
  ```bash
  daemonize no # docker容器启动方式需将后台守护线程设置为关闭
  requirepass ${password} # 设置被访问时所需的密码
  ```

  其余配置信息可参考[```redis.conf```](https://github.com/redis/redis/blob/unstable/redis.conf)官方模板。

* ```docker-compose.yaml```配置文件编写：
  
  ```bash
  version: '3'
  services:
    redis-master:
      image: redis:latest
      container_name: redis-master
      ports:
        - "16379:6379"
      networks:
        - redis-network #使用桥接网络
      volumes:
        - /data/redis/redis.conf:/etc/redis/redis.conf #挂载配置文件目录
        - /data/redis/rdb-master:/data #挂载数据保存目录
        - /data/redis/exp:/exp #挂载插件目录
      command: redis-server /etc/redis/redis.conf --masterauth ${password} --replica-announce-ip 114.132.78.39 --replica-announce-port 16379 #启动命令参数分别为指定配置文件、访问主服务器所需密码、暴露的可访问地址以及端口

    redis-slave1:
      image: redis:latest
      container_name: redis-slave1
      ports:
        - "16378:6379"
      networks:
        - redis-network #使用桥接网络
      volumes:
        - /data/redis/redis.conf:/etc/redis/redis.conf #挂载配置文件目录
        - /data/redis/rdb-slave1:/data #挂载数据保存目录
        - /data/redis/exp:/exp #挂载插件目录
      command: redis-server /etc/redis/redis.conf --slaveof redis-master 6379 --masterauth ${password} --replica-announce-ip 114.132.78.39 --replica-announce-port 16378 #启动命令参数分别为指定配置文件、绑定主服务器地址与端口（桥接模式可使用别名+映射端口，HOST模式则需宿主IP+宿主端口）、访问主服务器所需密码、暴露的可访问地址以及端口

    redis-slave2:
      image: redis:latest
      container_name: redis-slave2
      ports:
        - "16377:6379"
      networks:
        - redis-network #使用桥接网络
      volumes:
        - /data/redis/redis.conf:/etc/redis/redis.conf #挂载配置文件目录
        - /data/redis/rdb-slave2:/data #挂载数据保存目录
        - /data/redis/exp:/exp #挂载插件目录
      command: redis-server /etc/redis/redis.conf --slaveof redis-master 6379 --masterauth ${password} --replica-announce-ip 114.132.78.39 --replica-announce-port 16377 #启动命令参数分别为指定配置文件、绑定主服务器地址与端口（桥接模式可使用别名+映射端口，HOST模式则需宿主IP+宿主端口）、访问主服务器所需密码、暴露的可访问地址以及端口

  networks:
    redis-network:
      driver: bridge
  ```

  ！对于配置文件，每个主从服务都应该独立一份配置，上述共用同一份配置只为快速部署。

* 检查是否部署成功：

  ```bash
  # 进入master容器
  docker exec -it redis-master /bin/bash
  # 使用redis客户端，查看节点信息：
  redis-cli -a ${password} -h 127.0.0.1 -p 6379
  info replication
  ```

  若节点信息显示职责```role```为```master```，且同时出现```slave```节点信息则表情主从复制模式部署成功。

> 哨兵模式

```bash
version: '3'
services:
  redis-sentinel1:
    image: redis:latest
    container_name: redis-sentinel1
    ports:
      - "26379:26379"
    volumes:
      - /data/redis/sentinel.conf:/etc/redis/sentinel.conf
      - /data/redis/sentinel1:/data
    command: redis-sentinel /etc/redis/sentinel.conf

  redis-sentinel2:
    image: redis:latest
    container_name: redis-sentinel2
    ports:
      - "26378:26379"
    volumes:
      - /data/redis/sentinel.conf:/etc/redis/sentinel.conf
      - /data/redis/sentinel2:/data
    command: redis-sentinel /etc/redis/sentinel.conf

  redis-sentinel3:
    image: redis:latest
    container_name: redis-sentinel3
    ports:
      - "26377:26379"
    volumes:
      - /data/redis/sentinel.conf:/etc/redis/sentinel.conf
      - /data/redis/sentinel3:/data
    command: redis-sentinel /etc/redis/sentinel.conf

networks:
  default:
    external: true
    name: redis-master-slave_redis-network
```

> 集群模式

```bash
version: '3'
services:
  redis-6379:
    image: redis:latest
    container_name: redis-6379
    network_mode: "host"
    volumes:
      - /data/redis/redis-cluster-6379.conf:/etc/redis/redis.conf
      - /data/redis/redis-cluster-6379:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf

  redis-6378:
    image: redis:latest
    container_name: redis-6378
    network_mode: "host"
    volumes:
      - /data/redis/redis-cluster-6378.conf:/etc/redis/redis.conf
      - /data/redis/redis-cluster-6378:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf

  redis-6377:
    image: redis:latest
    container_name: redis-6377
    network_mode: "host"
    volumes:
      - /data/redis/redis-cluster-6377.conf:/etc/redis/redis.conf
      - /data/redis/redis-cluster-6377:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf

  redis-6376:
    image: redis:latest
    container_name: redis-6376
    network_mode: "host"
    volumes:
      - /data/redis/redis-cluster-6376.conf:/etc/redis/redis.conf
      - /data/redis/redis-cluster-6376:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf

  redis-6375:
    image: redis:latest
    container_name: redis-6375
    network_mode: "host"
    volumes:
      - /data/redis/redis-cluster-6375.conf:/etc/redis/redis.conf
      - /data/redis/redis-cluster-6375:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf

  redis-6374:
    image: redis:latest
    container_name: redis-6374
    network_mode: "host"
    volumes:
      - /data/redis/redis-cluster-6374.conf:/etc/redis/redis.conf
      - /data/redis/redis-cluster-6374:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf
```

```bash
redis-cli -a garden520 --cluster create 114.132.78.39:6379 114.132.78.39:6378 114.132.78.39:6377 114.132.78.39:6376 114.132.78.39:6375 114.132.78.39:6374 --cluster-replicas 1
```

> 存在问题

* org:redisson:redisson:2.15.2 不支持sentinel auth command，故redis sentinel config 未配置requirepass。
* docker compose 部署的 redis sentinel 只返回容器ip与端口，外网客户端无法访问。[已解决](https://blog.csdn.net/a1076067274/article/details/109263303)
  
  ```bash
  # redis server start command add these params
  --replica-announce-ip ${host_ip}
  --replica-announce-port ${host_port}

  # sentinel server start command add these params
  --sentinel announce-ip ${host_ip}
  --sentinel announce-port ${host_port}

  # sentinel.conf use host_ip and host_port
  sentinel monitor mymaster ${host_ip} ${host_port} 2
  ```