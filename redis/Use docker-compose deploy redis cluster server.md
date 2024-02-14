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
      - /data/redis/rdb:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf

  redis-slave1:
    image: redis:latest
    container_name: redis-slave1
    ports:
      - "16378:6379"
    networks:
      - redis-network
    volumes:
      - /data/redis/redis.conf:/etc/redis/redis.conf
      - /data/redis/rdb:/data
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
      - /data/redis/rdb:/data
      - /data/redis/exp:/exp
    command: redis-server /etc/redis/redis.conf --slaveof redis-master 6379 --masterauth garden520

networks:
  redis-network:
    driver: bridge
```