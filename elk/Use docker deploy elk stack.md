## 使用 docker 部署 elk stack

> 实现简单的 elk stack 的整体流程
![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-17_10-21-38.png)

> 实现环境

* 一台 CentOS 7.6.1810 2核8G
  * Docker version 20.10.17
  * docker-compose version 1.18.0
  * 部署的服务：

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-18_17-01-52.png)  

* 一台 CentOS 8.0.1905 2核4G
  * Docker version 20.10.18
  * Docker Compose version v2.4.1
  * 部署的服务：
    
    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-18_17-01-52.png)   

> 部署 elasticsearch

* 拉取镜像
  
  ```bash
  docker pull elasticsearch:7.17.9
  ```

* 创建存储配置、数据以及日志的目录并读写权限
  
  ```bash
  mkdir -p /data/elk/es/config && mkdir -p /data/elk/es/data && mkdir -p /data/elk/es/logs && chown -R 1000:1000 /data/elk/es
  ```

* 编写配置，设置集群名称、本地```host```以及端口并且开启```xpack.security```插件（用于设置访问账号密码）

  ```bash
  vim /data/elk/es/config/elasticsearch.yml

  cluster.name: "elasticsearch"
  network.host: 0.0.0.0
  http.port: 9200
  xpack.security.enabled: true
  ```

* 运行容器

  ```bash
  docker run --name elasticsearch --restart=always -d -p 9200:9200 -p 9300:9300 -e ES_JAVA_OPTS="-Xms512m -Xmx1024m" -e "discovery.type=single-node" -v /data/elk/es/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml -v /data/elk/es/data:/usr/share/elasticsearch/data -v /data/elk/es/logs:/usr/share/elasticsearch/logs elasticsearch:7.17.9
  ```

  使用```ES_JAVA_OPTS```环境变量指定```JVM```参数，使用```discovery.type```环境变量设置服务类型，本例使用的是单例```single-node```。最后需挂载配置文件、数据以及日志的数据卷。

* 进入容器设置访问账号密码
  
  ```bash
  docker exec -it elasticsearch /bin/bash

  cd bin

  elasticsearch-setup-passwords interactive
  ```

  设置密码的用户如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-17_15-27-58.png)

* 重启容器
  
  ```bash
  docker restart elasticsearch
  ```

* 验证部署是否成功，浏览器输入访问地址如```http://159.75.138.212:9200/```，输入访问账号密码，如```elastic/garden520```

> kibana

* 拉取镜像

  ```bash
  docker pull kibana:7.17.9
  ```

* 创建服务目录并赋予读写权限
  
  ```bash
  mkdir -p /data/elk/kibana && chown -R 1000:1000 /data/elk/kibana
  ```

* 查看```elasticsearch```容器```ip```，如```172.17.0.2```
  
  ```bash
  docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elasticsearch
  ```

* 编写配置，设置端口、服务名称以及本地```host```，指定```elasticsearch```访问地址以及账号密码，启动```xpack.monitoring.ui```插件以及设置系统字体为中文
  
  ```bash
  vim /data/elk/kibana/kibana.yml

  server.port: 5601
  server.name: kibana
  server.host: 0.0.0.0
  elasticsearch.hosts: ["http://172.17.0.2:9200"]
  elasticsearch.username: kibana
  elasticsearch.password: garden520
  xpack.monitoring.ui.container.elasticsearch.enabled: true
  i18n.locale: "zh-CN"
  ```

* 运行容器

  ```bash
  docker run --name kibana --restart=always --log-driver json-file --log-opt max-size=100m --log-opt max-file=2 -d -p 5601:5601 -v /data/elk/kibana/kibana.yml:/usr/share/kibana/config/kibana.yml kibana:7.17.9
  ```

* 验证是否部署成功，浏览器输入访问地址如```http://159.75.138.212:5601/```，输入访问账号密码，如```elastic/garden520```

> kafka

* 编写 ```kafka``` 集群的 ```kafka-docker-compose.yaml``` 文件

  ```bash
  version: "2"

  services:
    zookeeper:
      image: docker.io/bitnami/zookeeper:3.8
      user: root
      ports:
        - "2181:2181"
      volumes:
        - "/data/zookeeper_data:/bitnami"
      environment:
        - ALLOW_ANONYMOUS_LOGIN=yes
    kafka0:
      image: docker.io/bitnami/kafka:3.4
      container_name: kafka0
      user: root
      ports:
        - "9092:9092"
      volumes:
        - "/data/kafka0_data:/bitnami"
      environment:
        - KAFKA_BROKER_ID=0
        - KAFKA_ENABLE_KRAFT=no
        - ALLOW_PLAINTEXT_LISTENER=yes
        - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
        - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092
        - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://${宿主机IP}:9092
      depends_on:
        - zookeeper
    kafka1:
      image: docker.io/bitnami/kafka:3.4
      container_name: kafka1
      user: root
      ports:
        - "9093:9093"
      volumes:
        - "/data/kafka1_data:/bitnami"
      environment:
        - KAFKA_BROKER_ID=1
        - KAFKA_ENABLE_KRAFT=no
        - ALLOW_PLAINTEXT_LISTENER=yes
        - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
        - KAFKA_CFG_LISTENERS=PLAINTEXT://:9093
        - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://${宿主机IP}:9093
      depends_on:
        - zookeeper
    kafka2:
      image: docker.io/bitnami/kafka:3.4
      container_name: kafka2
      user: root
      ports:
        - "9094:9094"
      volumes:
        - "/data/kafka2_data:/bitnami"
      environment:
        - KAFKA_BROKER_ID=2
        - KAFKA_ENABLE_KRAFT=no
        - ALLOW_PLAINTEXT_LISTENER=yes
        - KAFKA_CFG_ZOOKEEPER_CONNECT=zookeeper:2181
        - KAFKA_CFG_LISTENERS=PLAINTEXT://:9094
        - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://${宿主机IP}:9094
      depends_on:
        - zookeeper
    kafka-ui:
      image: provectuslabs/kafka-ui:latest
      container_name: kafka-ui
      restart: always
      ports:
        - 18080:8080
      volumes:
        - /etc/localtime:/etc/localtime
      environment:
        - KAFKA_CLUSTERS_0_NAME=local
        - KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS=kafka0:9092,kafka1:9093,kafka2:9094
        - AUTH_TYPE=LOGIN_FORM
        - SPRING_SECURITY_USER_NAME=kafkaui
        - SPRING_SECURITY_USER_PASSWORD=garden520
  ```
  
  环境变量```KAFKA_CFG_LISTENERS=PLAINTEXT```设置内部监听方式，用于容器间内部互相访问；环境变量```KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT```设置客户端监听方式，用户客户端的访问，一般使用宿主机的内网或外网地址以及端口。环境变量```AUTH_TYPE```为设置```kafka-ui```权限类型，环境变量```SPRING_SECURITY_USER_NAME```与环境变量```SPRING_SECURITY_USER_PASSWORD```为设置```kafka-ui```登录账号密码。

* 运行编排的容器
  
  ```bash
  docker-compose -f kafka-docker-compose.yaml up -d
  ```

* 创建主题，进入任意```kafka```容器内，通过```kafka-topics.sh --create --topic```命令创建主题
  
  ```bash
  docker exec ${kafka_container_name} kafka-topics.sh --create --topic ${topic} --bootstrap-server ${kafka_container_name}:${kafka_conatiner_port} --partitions 3 --replication-factor 3
  ```
  
  ```--partitions```参数设置逻辑分区，```replication-factor```设置每个逻辑分区的副本数，通过这两个参数可以逻辑上编排```broker```，每个分区上都有一名```leader```职责的```broker```负责消息的写操作，其他则负责消息的读操作。

  或者登录```kafka-ui```创建主题，如```http://116.205.156.93:18080/```，账号密码为```kafkaui/garden520```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-19_15-13-59.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-19_15-20-38.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-19_15-20-38.png)

  查看主题，进入任意```kafka```容器内，通过```kafka-topics.sh --describe --topic```命令查看主题：

  ```bash
  docker exec ${kafka_container_name} kafka-topics.sh --describe --topic ${topic} --bootstrap-server ${kafka_container_name}:${kafka_conatiner_port}
  ```

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-26_16-18-42.png)

* 验证主题是否可用，通过进入任意```kafka```容器使用```kafka-console-producer.sh --topic```命令向主题生产推送消息，进入任意```kafka```容器使用```kafka-console-consumer.sh --topic```命令向主题订阅消费消息：

  ```bash
  docker exec -it ${kafka_container_name} sh
  kafka-console-producer.sh --topic ${topic} --bootstrap-server ${kafka_container_name}:${kafka_conatiner_port}
  ```

  ```bash
  docker exec -it ${kafka_container_name} sh
  kafka-console-consumer.sh --topic ${topic} --from-beginning --bootstrap-server ${kafka_container_name}:${kafka_conatiner_port}
  ```
  
  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-26_16-51-09.png)

> nginx

* [使用docker部署nginx](https://gitee.com/FSDGarden/learn-note/blob/master/nginx/Use%20docker%20deploy%20nginx.md)
* 修改配置文件```nginx.conf```
  
  ```bash
  user  nginx;
  worker_processes  auto;

  error_log  /var/log/nginx/error.log notice;
  pid        /var/run/nginx.pid;

  events {
      worker_connections  1024;
  }

  stream {
      upstream kafka {
          server 116.205.156.93:9092;
          server 116.205.156.93:9093;
          server 116.205.156.93:9094;
      }
      server {
          listen 80;
          proxy_pass kafka;
      }
  }

  http {
      include       /etc/nginx/mime.types;
      default_type  application/octet-stream;

      log_format  main  '$remote_addr - $remote_user [$time_local] "$request" '
                      '$status $body_bytes_sent "$http_referer" '
                      '"$http_user_agent" "$http_x_forwarded_for"';

      access_log  /var/log/nginx/access.log  main;

      sendfile        on;
      #tcp_nopush     on;

      keepalive_timeout  65;

      #gzip  on;

      #include /etc/nginx/conf.d/*.conf;
  }
  ```

> filebeat

* 拉取镜像

  ```bash
  docker pull docker.elastic.co/beats/filebeat:7.17.9
  ```

* 创建服务目录并赋予读写权限

  ```bash
  mkdir -p /data/elk/filebeat && chown -R 1000:1000 /data/elk/filebeat
  ```

* 编写配置文件```filebeat.yml```

  ```bash
  vim /data/elk/filebeat/filebeat.yml

  filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /usr/share/filebeat/logs/microservices-consumer/*
    fields:
      log_topic: consumer-log-topic
  - type: log
    enabled: true
    paths:
      - /usr/share/filebeat/logs/microservices-provider/*
    fields:
      log_topic: provider-log-topic
  
  output.kafka:
    enabled: true
    hosts: ["159.75.138.212:4000"]
    topic: '%{[fields.log_topic]}'
  ```

* 运行容器
  
  ```bash
  docker run --name filebeat -d -v /data/elk/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml -v /data/logs:/usr/share/filebeat/logs docker.elastic.co/beats/filebeat:7.17.9
  ```

 > logstash

 * 拉取镜像

  ```bash
  docker pull docker.elastic.co/logstash/logstash:7.17.9
  ```

* 创建服务目录并赋予读写权限

  ```bash
  mkdir -p /data/elk/logstash/config && mkdir -p /data/elk/logstash/pipeline && chown -R 1000:1000 /data/elk/logstash
  ```

* 查看```elasticsearch```容器```ip```，如```172.17.0.2```
  
  ```bash
  docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elasticsearch
  ```

* 编写服务配置文件```logstash.yml```

  ```bash
  vim /data/elk/logstash/config/logstash.yml

  config:
    reload:
      automatic: true
       interval: 3s
  xpack:
    management.enabled: false
    monitoring.enabled: false
  ```

* 编写管道映射文件以及管道配置文件
  
  ```bash
  vim /data/elk/logstash/config/pipelines.yml

  - pipeline.id: consumer_service_pipeline
    path.config: /usr/share/logstash/pipeline/consumer_service_pipeline.conf
  - pipeline.id: provider_service_pipeline
    path.config: /usr/share/logstash/pipeline/provider_service_pipeline.conf
  ```

  ```bash
  vim /data/elk/logstash/pipeline/consumer_service_pipeline.conf
  
  input {

    kafka {
      bootstrap_servers => "159.75.138.212:4000"
      topics => ["consumer-log-topic"]
      codec => "json"
    }

  }

  filter {

    grok {
      match => ["message", "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:logLevel} %{DATA:class} \[%{DATA:thread}\] %{GREEDYDATA:message}"]
      overwrite => ["message"]
    }

    mutate {
      lowercase => ["logLevel"]
      update => ["host", "host.name"]
    }
  
    date {
      match => ["timestamp" , "YYYY-MM-dd HH:mm:ss.SSS"]
      target => "@timestamp"
    }

    if [logLevel] == 'info' {
      mutate { add_field => { "[@metadata][target_index]" => "consumer-service-info-%{+YYYY.MM.dd}" } }
    } else if [logLevel] == 'error'{
      mutate { add_field => { "[@metadata][target_index]" => "consumer-service-error-%{+YYYY.MM.dd}" } }
    } else {
      mutate { add_field => { "[@metadata][target_index]" => "consumer-service-other-%{+YYYY.MM.dd}" } }
    }

  }
 
  output {

    stdout {}

    elasticsearch {
      hosts => ["172.17.0.2:9200"]
      index => "%{[@metadata][target_index]}"
      user => elastic
      password => garden520
    }

  }
  ```

  ```bash
  vim /data/elk/logstash/pipeline/provider_service_pipeline.conf

  input {

    kafka {
      bootstrap_servers => "159.75.138.212:4000"
      topics => ["provider-log-topic"]
      codec => "json"
    }
    
  }

  filter {

    grok {
      match => ["message", "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:logLevel} %{DATA:class} \[%{DATA:thread}\] %{GREEDYDATA:message}"]
      overwrite => ["message"]
    }

    mutate {
      lowercase => ["logLevel"]
      update => ["host", "host.name"]
    }
  
    date {
      match => ["timestamp" , "YYYY-MM-dd HH:mm:ss.SSS"]
      target => "@timestamp"
    }

    if [logLevel] == 'info' {
      mutate { add_field => { "[@metadata][target_index]" => "provider-service-info-%{+YYYY.MM.dd}" } }
    } else if [logLevel] == 'error'{
      mutate { add_field => { "[@metadata][target_index]" => "provider-service-error-%{+YYYY.MM.dd}" } }
    } else {
      mutate { add_field => { "[@metadata][target_index]" => "provider-service-other-%{+YYYY.MM.dd}" } }
    }

  }
 
  output {

    stdout {}

    elasticsearch {
      hosts => ["172.17.0.2:9200"]
      index => "%{[@metadata][target_index]}"
      user => elastic
      password => garden520
    }

  }
  ```

* 运行容器
  
  ```bash
  docker run -d --name logstash --restart=always --privileged=true -p 5047:5047 -p 9600:9600 -v /data/elk/logstash/pipeline/:/usr/share/logstash/pipeline/ -v /data/elk/logstash/config/:/usr/share/logstash/config/ docker.elastic.co/logstash/logstash:7.17.9
  ```

> 验证 elk stack 是否搭建成功
  
  * 使用```curl```调用```consumner-service```接口

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-18_16-47-54.png) 
  
  * 登录 ```kibana```，如访问地址```http://159.75.138.212:5601/```，账号密码```elastic/garden520```。创建索引并查看```Discover```对应索引下的服务日志信息

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-18_16-43-35.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-18_16-45-35.png)

    ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-18_16-46-52.png)

> [相关日志与对应的logstash管道配置](https://gitee.com/FSDGarden/learn-note/tree/master/elk/log2logstashPipelineConfig)

> 存在问题
  
* ```logstash```的```pipeline```配置中，```host```字段未能获取业务服务具体的```host```。
* ```logstash```输出到```elasticsearch```以及```kibana```注册到```elasticsearch```都使用```elasticsearch```容器```ip```端口，```docker```进程重启后```elasticsearch```容器```ip```可能会发生改变，每次重启后需要检查```elasticsearch```容器```ip```，若改变需修改```logstash```的管道输出配置以及```kibana```注册至```elasticsearch```。

> 问题解决

* 问题2可使用```docker-compose```将```elasticsearch```、```logstash```以及```kibana```容器进行编排，```logstash```输出到```elasticsearch```以及```kibana```注册到```elasticsearch```的地址都可使用```serviceName```，```docker-compose```如下：

  ```bash
  version: '2'
  services:
    elasticsearch:
      container_name: elasticsearch
      image: elasticsearch:7.17.9
      ports:
        - 9200:9200
        - 9300:9300
      expose:
        - 9200
        - 9300
      volumes:
        - /data/elk/es/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
        - /data/elk/es/data:/usr/share/elasticsearch/data
        - /data/elk/es/logs:/usr/share/elasticsearch/logs
      environment:
        - "ES_JAVA_OPTS=-Xms512m -Xmx1024m"
        - "discovery.type=single-node"
      restart: always
      networks:
        - elk

    kibana:
      container_name: kibana
      image: kibana:7.17.9
      ports:
        - 5601:5601
      expose:
        - 5601
      volumes:
        - /data/elk/kibana/kibana.yml:/usr/share/kibana/config/kibana.yml
      restart: always
      networks:
        - elk
      depends_on:
        - elasticsearch

    logstash:
      container_name: logstash
      image: docker.elastic.co/logstash/logstash:7.17.9
      ports:
        - "5047:5047"
        - "9600:9600"
      expose:
        - 5047
        - 9600
      volumes:
        - /data/elk/logstash/pipeline/:/usr/share/logstash/pipeline/
        - /data/elk/logstash/config/:/usr/share/logstash/config/
      restart: always
      networks:
        - elk
      depends_on:
        - elasticsearch

  networks:
    elk:
      driver: bridge
  ```

  ```kibana```的配置修改如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-25_15-23-03.png)

  ```logstash```的```consumer```以及```provider```的```pipeline```配置修改如下：

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-25_15-25-04.png)

  ![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-05-25_15-27-00.png)

> 参考文献

* [一文带你搭建一套 ELK Stack 日志平台](https://www.51cto.com/article/707776.html)
* [一口气完成ELK 日志平台的搭建，我感觉我又行了!](https://juejin.cn/post/7157596325918277663)
* [支持一览表](https://www.elastic.co/cn/support/matrix#matrix_os)
* [带你理清kafka术语](https://juejin.cn/post/7165844594817499166)
* [bitnami/kafka](https://hub.docker.com/r/bitnami/kafka)
* [Kafka Listeners - Explained](https://rmoff.net/2018/08/02/kafka-listeners-explained/)
* [Kafka:用nginx做kafka集群代理（非http）](https://cloud.tencent.com/developer/article/1750382)
* [利用nginx的stream模块实现内网端口的转发代理](https://www.linuxprobe.com/nginx-linux-stream.html)
* [Logstash 最佳实践](https://doc.yonyoucloud.com/doc/logstash-best-practice-cn/index.html)
* [Grok Constructor](http://grokconstructor.appspot.com/do/match#result)
* [kyungw00k/logback.xml](https://gist.github.com/kyungw00k/e7b3cee94d9c669e5586)
* [plugins-outputs-elasticsearch.html#_writing_to_different_indices_best_practices](https://www.elastic.co/guide/en/logstash/7.17/plugins-outputs-elasticsearch.html#_writing_to_different_indices_best_practices)
* [Filebeats input多个log文件，输出Kafka多个topic配置](https://www.cnblogs.com/saneri/p/15919227.html)
* [UI for Apache Kafka Quick Start](https://docs.kafka-ui.provectus.io/configuration/quick-start)
* [Integrate Filebeat, Kafka, Logstash, Elasticsearch And Kibana](https://github.com/eunsour/docker-elk)