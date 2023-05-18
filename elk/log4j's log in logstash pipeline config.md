## log4j日志 在 logstash 的管道配置

> log4j日志样例：
  
```bash
2023-05-05 15:37:55,103 INFO com.garden.springbootlogging.SpringbootLoggingApplicationTests [main] loggerTest => log4j2 testing
2023-05-05 15:37:55,103 ERROR com.garden.springbootlogging.SpringbootLoggingApplicationTests [main] loggerTest => log4j2 err
```

> logstash管道配置

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
    mutate { add_field => { "[@metadata][target_index]" => "log4j_dev-info-%{+YYYY.MM.dd}" } }
  } else if [logLevel] == 'error'{
    mutate { add_field => { "[@metadata][target_index]" => "log4j_dev-error-%{+YYYY.MM.dd}" } }
  } else {
    mutate { add_field => { "[@metadata][target_index]" => "log4j_dev-other-%{+YYYY.MM.dd}" } }
  }

}

output {
  stdout {}
  elasticsearch {
    hosts => ["172.17.0.3:9200"]
    index => "%{[@metadata][target_index]}"
  }
}
```
