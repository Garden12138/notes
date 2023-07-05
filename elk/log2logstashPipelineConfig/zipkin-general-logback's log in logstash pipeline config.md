## zipkin 常规 logback 日志 在 logstash 的管道配置

> zipkin 常规 logback 日志格式设置（SpringBoot框架自带，无需设置）：

```bash
%d{yyyy-MM-dd HH:mm:ss.SSS} ${LOG_LEVEL_PATTERN:-%5p} ${PID:- } --- [%thread] %logger{39}: %msg%n
```

> zipkin 常规 logback 日志样例：
  
```bash
2023-07-04 16:59:37.721  INFO [consumer,270d1d8fa4a7104a,270d1d8fa4a7104a] 16412 --- [nio-8763-exec-1] c.g.c.s.impl.SeataBusinessServiceImpl    : 购买下单结束...
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
    match => ["message", "%{TIMESTAMP_ISO8601:timestamp}  %{LOGLEVEL:logLevel} \[%{DATA:service},%{DATA:trace},%{DATA:span}\] %{NUMBER:tid} --- \[%{DATA:thread}\] %{DATA:class} :\s+(?<message>.*)"]
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
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_logback_general-info-%{+YYYY.MM.dd}" } }
  } else if [logLevel] == 'error'{
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_logback_general-error-%{+YYYY.MM.dd}" } }
  } else {
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_logback_general-other-%{+YYYY.MM.dd}" } }
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
