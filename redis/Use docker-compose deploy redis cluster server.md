## 使用 docker-compose 部署 redis 集群服务

> 主从复制

```bash
version: '3'
services:
  redis-master:
    image: redis:latest
    container_name: redis-master
    ports:
      - "16379:6379"
    networks:
      - redis-network
    volumes:
      - /data/redis/redis.conf:/etc/redis/redis.conf
      - /data/redis/rdb-master:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf --masterauth garden520

  redis-slave1:
    image: redis:latest
    container_name: redis-slave1
    ports:
      - "16378:6379"
    networks:
      - redis-network
    volumes:
      - /data/redis/redis.conf:/etc/redis/redis.conf
      - /data/redis/rdb-slave1:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf --slaveof redis-master 6379 --masterauth garden520

  redis-slave2:
    image: redis:latest
    container_name: redis-slave2
    ports:
      - "16377:6379"
    networks:
      - redis-network
    volumes:
      - /data/redis/redis.conf:/etc/redis/redis.conf
      - /data/redis/rdb-slave2:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf --slaveof redis-master 6379 --masterauth garden520

networks:
  redis-network:
    driver: bridge
```

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