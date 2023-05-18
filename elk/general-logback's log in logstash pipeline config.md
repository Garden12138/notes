## 常规 logback 日志 在 logstash 的管道配置

> 常规 logback 日志样例：
  
```bash
2023-05-14 17:55:51.109  INFO 16080 --- [main] c.g.s.SpringbootLoggingApplicationTests  : lombokTest => logback testing
2023-05-14 18:11:52.109  ERROR 16080 --- [main] c.g.s.SpringbootLoggingApplicationTests  : lombokTest => logback err
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
    match => ["message", "%{TIMESTAMP_ISO8601:timestamp}  %{LOGLEVEL:logLevel} %{NUMBER:tid} --- \[%{DATA:thread}\] %{DATA:class} :\s+(?<message>.*)"]
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
    mutate { add_field => { "[@metadata][target_index]" => "logback_general-dev-info-%{+YYYY.MM.dd}" } }
  } else if [logLevel] == 'error'{
    mutate { add_field => { "[@metadata][target_index]" => "logback_general-dev-error-%{+YYYY.MM.dd}" } }
  } else {
    mutate { add_field => { "[@metadata][target_index]" => "logback_general-dev-other-%{+YYYY.MM.dd}" } }
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
