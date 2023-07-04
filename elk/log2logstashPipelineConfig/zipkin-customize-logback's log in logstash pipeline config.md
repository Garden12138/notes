## zipkin 自定义 logback 日志 在 logstash 的管道配置

> zipkin 自定义 logback 日志格式设置：

```bash
[%d{yyyy-MM-dd HH:mm:ss.SSS}] ${LOG_LEVEL_PATTERN} [${HOSTNAME}] [%thread] %logger{36}@%method:%line - %msg%n
```

> zipkin 自定义 logback 日志样例：
  
```bash
[2023-07-04 12:25:56.774]  INFO [consumer,3c5832ee16baa318,3c5832ee16baa318] [WINDOWS-ECSBFQF] [http-nio-8763-exec-1] c.g.c.s.i.SeataBusinessServiceImpl@purchase:28 - 购买下单结束...
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
    match => ["message", "(?m)\[%{TIMESTAMP_ISO8601:timestamp}\]  %{LOGLEVEL:logLevel} \[%{DATA:service},%{DATA:trace},%{DATA:span}\] \[%{HOSTNAME:host}\] \[%{DATA:thread}\] %{DATA:class}@%{DATA:method}:%{DATA:line} \- %{GREEDYDATA:message}"]
    overwrite => ["host", "message"]
  }

  mutate {
    add_field => {
      "code" => "%{thread}-%{class}@%{method}:%{line}"
    }
    remove_field => ["thread", "class", "method", "line"]
    lowercase => ["logLevel"]
  }

  date {
    match => ["timestamp" , "YYYY-MM-dd HH:mm:ss.SSS"]
    target => "@timestamp"
  }

  if [logLevel] == 'info' {
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_logback_customize-info-%{+YYYY.MM.dd}" } }
  } else if [logLevel] == 'error'{
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_logback_customize-error-%{+YYYY.MM.dd}" } }
  } else {
    mutate { add_field => { "[@metadata][target_index]" => "zipkin_logback_customize-other-%{+YYYY.MM.dd}" } }
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
