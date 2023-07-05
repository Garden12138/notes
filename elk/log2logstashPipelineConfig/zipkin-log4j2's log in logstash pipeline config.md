## zipkin log4j2 日志 在 logstash 的管道配置

> zipkin log4j2 日志格式设置：

```bash
%d [${spring:spring.application.name},%X{traceId},%X{spanId}] %p %C{} [%t] %m%n
```

> zipkin log4j2 日志样例：
  
```bash
2023-07-05 14:14:44,489 [consumer,6e02b3a054b56deb,6e02b3a054b56deb] INFO com.garden.consumer.service.impl.SeataBusinessServiceImpl [http-nio-8763-exec-1] 购买下单结束...
```

> logstash 管道配置

```bash
input {
  kafka {
    bootstrap_servers => "159.75.138.212:4000"
    topics => ["kafka-test-topic"]
    codec => "json"
  }
}

filter {

  grok {
    match => ["message", "%{TIMESTAMP_ISO8601:timestamp} \[%{DATA:service},%{DATA:trace},%{DATA:span}\] %{LOGLEVEL:logLevel} %{DATA:class} \[%{DATA:thread}\] %{GREEDYDATA:message}"]
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
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_log4j2-info-%{+YYYY.MM.dd}" } }
  } else if [logLevel] == 'error'{
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_log4j2-error-%{+YYYY.MM.dd}" } }
  } else {
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_log4j2-other-%{+YYYY.MM.dd}" } }
  }

}

output {
  stdout {}
  elasticsearch {
    hosts => ["172.17.0.3:9200"]
    index => "%{[@metadata][target_index]}"
    user => elastic
    password => garden520
  }
}
```
