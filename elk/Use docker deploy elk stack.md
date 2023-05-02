## 使用 docker-compose 部署 elk stack

> elasticsearch

docker pull elasticsearch:7.17.9

mkdir -p /data/elk/es/config && mkdir -p /data/elk/es/data && mkdir -p /data/elk/es/logs && chown -R 1000:1000 /data/elk/es

vim /data/elk/es/config/elasticsearch.yml
```
cluster.name: "elasticsearch"
network.host: 0.0.0.0
http.port: 9200
```

docker run --name elasticsearch --restart=always -d -p 9200:9200 -p 9300:9300 -e ES_JAVA_OPTS="-Xms512m -Xmx1024m" -e "discovery.type=single-node" -v /data/elk/es/config/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml -v /data/elk/es/data:/usr/share/elasticsearch/data -v /data/elk/es/logs:/usr/share/elasticsearch/logs elasticsearch:7.17.9

local_console:
curl http:127.0.0.1:9200/

> kibana

docker pull kibana:7.17.9

mkdir -p /data/elk/kibana && chown -R 1000:1000 /data/elk/kibana

docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elasticsearch

vim /data/elk/kibana/kibana.yml
```
server.port: 5601
server.name: kibana
server.host: 0.0.0.0
elasticsearch.hosts: ["http://172.17.0.2:9200"]
## elasticsearch.username: es-admin
## elasticsearch.password: nXxDlKe0n4O7wSn
xpack.monitoring.ui.container.elasticsearch.enabled: true
i18n.locale: "zh-CN"
```

docker run --name kibana --restart=always --log-driver json-file --log-opt max-size=100m --log-opt max-file=2 -d -p 5601:5601 -v /data/elk/kibana/kibana.yml:/usr/share/kibana/config/kibana.yml kibana:7.17.9

browser:
${IP}:5601/

> filebeat

docker pull docker.elastic.co/beats/filebeat:7.17.9

mkdir -p /data/elk/filebeat && chown -R 1000:1000 /data/elk/filebeat

#docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' logstash
docker inspect --format='{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' elasticsearch

vim /data/elk/filebeat/filebeat.yml
```
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /usr/share/filebeat/logs/*

# output.logstash:
#  hosts: ["172.17.0.5:9900"]
  
  
output.elasticsearch: 
  hosts: ["172.17.0.2:9200"]  
```

 docker run --name filebeat -d -v /data/elk/filebeat/filebeat.yml:/usr/share/filebeat/filebeat.yml -v /root/logs:/usr/share/filebeat/logs docker.elastic.co/beats/filebeat:7.17.9

 docker logs -f --tail 200 filebeat

 curl http://127.0.0.1:9200/_cat/indices?v

 > logstash

 docker pull docker.elastic.co/logstash/logstash:7.17.9

 mkdir -p /data/elk/logstash/config && mkdir -p /data/elk/logstash/pipeline && chown -R 1000:1000 /data/elk/logstash

 vim /data/elk/logstash/config/logstash.yml
 ```
 config:
   reload:
     automatic: true
     interval: 3s
 xpack:
   management.enabled: false
   monitoring.enabled: false
 ```

 vim /data/elk/logstash/config/pipelines.yml
 ```
 - pipeline.id: logstash_dev
   path.config: /usr/share/logstash/pipeline/logstash_dev.conf
 ```

 vim /data/elk/logstash/pipeline/logstash_dev.conf
```
input {
  beats {
    port => 9900
  }
}
 
filter {
  grok {
    match => { "message" => "%{COMBINEDAPACHELOG}" }
  }
 
  mutate {
    convert => {
      "bytes" => "integer"
    }
  }
 
  geoip {
    source => "clientip"
  }
 
  useragent {
    source => "user_agent"
    target => "useragent"
  }
 
  date {
    match => ["timestamp", "dd/MMM/yyyy:HH:mm:ss Z"]
  }
}
 
output {
  stdout { }
 
  elasticsearch {
    hosts => ["172.17.0.2:9200"]
    index => "logstash_example"
  }
} 
```

docker run -d --name logstash --restart=always --privileged=true -p 5047:5047 -p 9600:9600 -v /data/elk/logstash/pipeline/:/usr/share/logstash/pipeline/ -v /data/elk/logstash/config/:/usr/share/logstash/config/ docker.elastic.co/logstash/logstash:7.17.9

docker logs -f --tail 200 logstash

vim /data/elk/filebeat/filebeat.yml
```
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /usr/share/filebeat/logs/*

output.logstash:
  hosts: ["172.17.0.5:9900"]
```

curl http://127.0.0.1:9200/_cat/indices?v

vim weblog-sample.log
```bash
14.49.42.25 - - [12/May/2019:01:24:44 +0000] "GET /articles/ppp-over-ssh/ 
HTTP/1.1" 200 18586 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; 
rv:1.9.2b1) Gecko/20091014 Firefox/3.6b1 GTB5"
```

> kafka

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
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://127.0.0.1:9092
    depends_on:
      - zookeeper
  kafka1:
    image: docker.io/bitnami/kafka:3.4
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
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://127.0.0.1:9093
    depends_on:
      - zookeeper
  kafka2:
    image: docker.io/bitnami/kafka:3.4
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
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://127.0.0.1:9094
    depends_on:
      - zookeeper
```

docker exec kafka-kafka0-1 kafka-topics.sh --create --topic kafka-test-topic --bootstrap-server kafka-kafka0-1:9092 --partitions 3 --replication-factor 3
docker exec kafka-kafka0-1 kafka-topics.sh --describe --topic kafka-test-topic --bootstrap-server kafka-kafka0-1:9092 --partitions 3 --replication-factor 3

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-26_16-18-42.png)

docker exec -it kafka-kafka0-1 sh
kafka-console-producer.sh --topic kafka-test-topic --bootstrap-server kafka-kafka0-1:9092
docker exec -it garden_kafka0_1 sh
kafka-console-producer.sh --topic kafka-test-topic --bootstrap-server garden_kafka0_1:9092


docker exec -it kafka-kafka1-1 sh
kafka-console-consumer.sh --topic kafka-test-topic --from-beginning --bootstrap-server kafka-kafka1-1:9093
docker exec -it garden_kafka1_1 sh
kafka-console-consumer.sh --topic kafka-test-topic --from-beginning --bootstrap-server garden_kafka1_1:9093

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-26_16-51-09.png)

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-27_15-59-05.png)

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-27_15-59-32.png)

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-27_15-56-42.png)

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-27_15-57-43.png)

![](https://raw.githubusercontent.com/Garden12138/picbed-cloud/main/minikube/Snipaste_2023-04-27_15-58-29.png)

> nginx

```
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

kafka-topics.sh --describe --topic kafka-test-topic --bootstrap-server 159.75.138.212:4000
kafka-topics.sh --describe --topic kafka-test-topic --bootstrap-server garden_kafka0_1:9092
kafka-topics.sh --describe --topic kafka-test-topic --bootstrap-server 116.205.156.93:9092

> 参考文献

* [一文带你搭建一套 ELK Stack 日志平台](https://www.51cto.com/article/707776.html)
* [一口气完成ELK 日志平台的搭建，我感觉我又行了!](https://juejin.cn/post/7157596325918277663)
* [支持一览表](https://www.elastic.co/cn/support/matrix#matrix_os)
* [Kafka:用nginx做kafka集群代理（非http）](https://cloud.tencent.com/developer/article/1750382)
* [利用nginx的stream模块实现内网端口的转发代理](https://www.linuxprobe.com/nginx-linux-stream.html)