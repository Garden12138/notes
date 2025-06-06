## 使用docker-compose部署RocketMQ

### 前提条件

* [docker](https://gitee.com/FSDGarden/learn-note/blob/master/docker/Install%20dokcer%20on%20centos.md)
* [docker-compose](https://gitee.com/FSDGarden/learn-note/blob/master/docker/Install%20docker-compose%20on%20centos.md)

### 部署步骤RocketMQ4.x版本

* 配置```broker.conf```文件：

  ```bash
  # 配置broker的IP地址
  echo "brokerIP1=127.0.0.1" > broker.conf
  ```

* 编写```docker-compose.yaml```文件：

  ```yaml
  version: '3.8'

  services:
    namesrv:
      image: apache/rocketmq:4.9.6
      container_name: rmqnamesrv
      ports:
        - 9876:9876
      networks:
        - rocketmq
      command: sh mqnamesrv

    broker:
      image: apache/rocketmq:4.9.6
      container_name: rmqbroker
      ports:
        - 10909:10909
        - 10911:10911
        - 10912:10912
      environment:
        - NAMESRV_ADDR=rmqnamesrv:9876
      volumes:
        - ./broker.conf:/home/rocketmq/rocketmq-4.9.6/conf/broker.conf
      depends_on:
        - namesrv
      networks:
        - rocketmq
      command: sh mqbroker -c /home/rocketmq/rocketmq-4.9.6/conf/broker.conf

  networks:
    rocketmq:
      driver: bridge
  ```

* 启动RocketMQ集群：

  ```bash
  docker-compose up -d
  ```

* 验证部署结果：

  ```bash
  # 进入broker容器
  docker exec -it rmqbroker bash
  # 生产示例消息
  sh tools.sh org.apache.rocketmq.example.quickstart.Producer
  # 消费示例消息
  sh tools.sh org.apache.rocketmq.example.quickstart.Consumer
  ```

### 参考文献

* [Docker Compose 部署 RocketMQ](https://rocketmq.apache.org/zh/docs/4.x/quickstart/03quickstartWithDockercompose/)